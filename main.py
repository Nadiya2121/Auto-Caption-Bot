import os
import re
import asyncio
import logging
import time
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from motor.motor_asyncio import AsyncIOMotorClient

# ==========================================
# ১. প্রফেশনাল লগিং সেটআপ
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# ২. কনফিগারেশন (Environment Variables)
# ==========================================
API_ID = int(os.environ.get("API_ID", "29462738"))
API_HASH = os.environ.get("API_HASH", "297f51aaab99720a09e80273628c3c24")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8673154872:AAHqVYxzUeJ2iAXdV8AGrDTPG0pDb2_UxAA")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://larib82632:larib82632@cluster0.rj7ed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ==========================================
# ৩. ডাটাবেস ও ওয়েব সার্ভার কানেকশন
# ==========================================
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Final_AutoCaption_Pro"]
cap_collection = db["channel_configs"]

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🔥 Bot is Online and Healthy! Powered by Flask System."

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ৪. স্মার্ট এক্সট্রাকশন ইউটিলিটি (Detailed Brain)
# ==========================================

def get_clean_filename(file_name):
    """মুভি এবং ওয়েব সিরিজের নাম ক্লিন করা (এপিসোড রেঞ্জ সাপোর্ট সহ)"""
    name, ext = os.path.splitext(file_name)
    
    # প্রাথমিক ক্লিনআপ (ডট, আন্ডারস্কোর সরিয়ে স্পেস দেওয়া)
    name = name.replace(".", " ").replace("_", " ").replace("-", " ")
    
    # সিজন এবং এপিসোড প্যাটার্ন (নিখুঁত ডিটেকশন)
    season_pattern = r'([sS]eason\s?\d+|[sS]\d+)'
    episode_pattern = r'(\[?[eE](pisode|p)?\s?\d+[\s\-\~\&to]*\d+\]?)'
    year_pattern = r'(19|20)\d{2}'

    found_season = re.search(season_pattern, name, re.IGNORECASE)
    found_episode = re.search(episode_pattern, name, re.IGNORECASE)
    found_year = re.search(year_pattern, name)

    clean_name = name
    info_tag = ""

    # সিরিজ ডিটেকশন
    if found_season or found_episode:
        cut_idx = len(name)
        if found_season:
            cut_idx = min(cut_idx, found_season.start())
            info_tag += " " + found_season.group(0).upper()
        if found_episode:
            if not found_season:
                cut_idx = min(cut_idx, found_episode.start())
            ep_text = found_episode.group(0).upper().replace('[', '').replace(']', '').strip()
            info_tag += f" [{ep_text}]"
        clean_name = name[:cut_idx]
    
    # মুভি ডিটেকশন
    elif found_year:
        year_idx = found_year.start()
        clean_name = name[:year_idx]
        info_tag = found_year.group(0)

    # জঞ্জাল শব্দ রিমুভ করার বিশাল লিস্ট
    junk_words = [
        '720p', '1080p', '480p', '2160p', '4k', 'hevc', 'h264', 'h265', 'x264', 'x265',
        '10bit', 'web-dl', 'webdl', 'bluray', 'hdrip', 'brrip', 'nf', 'web', 'dl', 'aac',
        'esub', 'sub', 'dual', 'multi', 'hdtv', 'proper', 'repack', 'combined', 'swapnonil',
        'hindi', 'english', 'bangla', 'tamil', 'telugu', 'kannada', 'malayalam', 'marathi',
        'korean', 'japanese', 'chinese', 'punjabi', 'gujarati', 'urdu', 'spanish', 'french'
    ]
    
    for word in junk_words:
        clean_name = re.sub(rf'\b{word}\b', '', clean_name, flags=re.IGNORECASE)
    
    final_title = ' '.join(clean_name.split())
    if info_tag:
        return f"{final_title} {info_tag.strip()}"
    return final_title

def get_smart_quality(name):
    """ভিডিও কোয়ালিটি শনাক্তকরণ"""
    name = name.lower()
    if "2160" in name or "4k" in name: return "4K UHD"
    if "1080" in name: return "1080p Full HD"
    if "720" in name: return "720p HD"
    if "480" in name: return "480p SD"
    if "cam" in name: return "CAMRip"
    if "hdtv" in name: return "HDTV"
    if "bluray" in name: return "BluRay"
    return "WEB-DL"

def get_advanced_audio(file_name):
    """দুনিয়ার সব ল্যাঙ্গুয়েজ ডিটেক্ট করার জন্য বিশাল ডাটাবেস লজিক"""
    n = file_name.lower()
    a = []
    
    # ১. এশিয়ান ল্যাঙ্গুয়েজ
    if any(x in n for x in ['hindi', 'hin', 'hnd']): a.append("Hindi")
    if any(x in n for x in ['bangla', 'ben', 'bd', 'bengali']): a.append("Bangla")
    if any(x in n for x in ['tamil', 'tam', 'tamily']): a.append("Tamil")
    if any(x in n for x in ['telugu', 'tel']): a.append("Telugu")
    if any(x in n for x in ['kannada', 'kan', 'kn']): a.append("Kannada")
    if any(x in n for x in ['malayalam', 'mal']): a.append("Malayalam")
    if any(x in n for x in ['marathi', 'mar']): a.append("Marathi")
    if any(x in n for x in ['punjabi', 'pun', 'pb']): a.append("Punjabi")
    if any(x in n for x in ['gujarati', 'guj']): a.append("Gujarati")
    if any(x in n for x in ['urdu', 'urd']): a.append("Urdu")
    if any(x in n for x in ['bhojpuri', 'bho']): a.append("Bhojpuri")
    
    # ২. ইন্টারন্যাশনাল (ইউরোপ ও আমেরিকা)
    if any(x in n for x in ['english', 'eng', 'en']): a.append("English")
    if any(x in n for x in ['spanish', 'spa', 'esp']): a.append("Spanish")
    if any(x in n for x in ['french', 'fre', 'fra']): a.append("French")
    if any(x in n for x in ['russian', 'rus']): a.append("Russian")
    if any(x in n for x in ['german', 'ger', 'deu']): a.append("German")
    if any(x in n for x in ['italian', 'ita']): a.append("Italian")
    if any(x in n for x in ['portuguese', 'por']): a.append("Portuguese")
    
    # ৩. ইস্ট এশিয়ান (Anime/K-Drama)
    if any(x in n for x in ['korean', 'kor', 'k-drama']): a.append("Korean")
    if any(x in n for x in ['japanese', 'jap', 'anime']): a.append("Japanese")
    if any(x in n for x in ['chinese', 'chi']): a.append("Chinese")
    if any(x in n for x in ['thai', 'tha']): a.append("Thai")
    
    # ৪. মিডল ইস্ট
    if any(x in n for x in ['arabic', 'ara']): a.append("Arabic")
    if any(x in n for x in ['turkish', 'tur']): a.append("Turkish")
    
    # ৫. স্পেশাল অডিও ট্যাগ
    is_dual = any(x in n for x in ['dual', '2-audio', 'd-audio'])
    is_multi = any(x in n for x in ['multi', 'm-audio', 'auds'])
    
    # রেজাল্ট প্রসেসিং
    if a:
        # ডুপ্লিকেট সরানো
        unique_audio = list(set(a))
        res = " | ".join(unique_audio)
        if len(unique_audio) >= 3:
            return f"Multi Audio [{res}]"
        return res
    
    if is_multi: return "Multi Audio"
    if is_dual: return "Dual Audio (Hindi-English)"
    
    # ডিফল্ট লজিক: যদি একদমই কিছু না পাওয়া যায়
    return "Hindi"

def get_readable_size(size):
    """ফাইলের সাইজ রিডাবল করা"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# ==========================================
# ৫. টেলিগ্রাম বট ফাংশনালিটি
# ==========================================
app = Client("smart_caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    example = (
        "🎬 **Movie:** Tu Yaa Main 2026\n"
        "🌟 **Quality:** 720p HD\n"
        "🔊 **Audio:** Hindi | English\n"
        "📁 **Size:** 1.25 GB\n\n"
        "✅ **Join: @YourChannel**"
    )
    
    start_text = (
        f"👋 **হ্যালো {message.from_user.mention}!**\n\n"
        "আমি একটি অ্যাডভান্সড **মাল্টি-চ্যানেল অটো ক্যাপশন বট**।\n\n"
        "🚀 **কিভাবে ব্যবহার করবেন?**\n"
        "১. আপনার চ্যানেলে আমাকে অ্যাডমিন করুন (Edit Message পারমিশন সহ)।\n"
        "২. বটের ইনবক্সে নিচের কমান্ডটি ব্যবহার করে ক্যাপশন সেট করুন:\n\n"
        "`/set_caption [Channel_ID] [Your_Caption]`\n\n"
        "📑 **ক্যাপশনে ব্যবহারযোগ্য ট্যাগসমূহ:**\n"
        "• `{filename}` - ক্লিন মুভি/সিরিজ নাম (E01-16 রেঞ্জ ডিটেক্ট করবে)\n"
        "• `{quality}` - ভিডিও কোয়ালিটি\n"
        "• `{audio}` - অডিও ল্যাঙ্গুয়েজ\n"
        "• `{size}` - ফাইলের সাইজ\n\n"
        "💡 **নিচের উদাহরণটি দেখে আইডি পরিবর্তন করে ব্যবহার করুন:**"
    )
    
    await message.reply_text(start_text)
    await asyncio.sleep(1)
    await message.reply_text(f"**উদাহরণ ফরম্যাট:**\n\n`/set_caption -100xxxxxxxx {example}`")
    await asyncio.sleep(1)
    await message.reply_text(f"**আপনার চ্যানেলে এটি নিচের মতো দেখাবে:**\n\n{example}")

@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ **ভুল কমান্ড!**\nব্যবহার: `/set_caption [Channel ID] [Caption]`")
    
    try:
        channel_id = int(message.command[1])
        caption_text = message.text.split(None, 2)[2]
        
        await cap_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"caption_text": caption_text}},
            upsert=True
        )
        await message.reply_text(f"✅ **অভিনন্দন!**\nচ্যানেল `{channel_id}` এর জন্য ক্যাপশন সেট করা হয়েছে।")
    except ValueError:
        await message.reply_text("❌ চ্যানেল আইডি অবশ্যই সংখ্যা হতে হবে (উদা: -100xxx)")
    except Exception as e:
        await message.reply_text(f"⚠️ এরর: {e}")

@app.on_message(filters.channel & (filters.video | filters.document))
async def auto_caption(client, message):
    chat_id = message.chat.id
    file = message.video or message.document
    if not file: return

    # ডাটাবেস থেকে কনফিগারেশন চেক
    config = await cap_collection.find_one({"channel_id": chat_id})
    if config:
        template = config["caption_text"]
    else:
        template = "🎬 **Name:** {filename}\n🌟 **Quality:** {quality}\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"

    raw_name = file.file_name if file.file_name else "Unknown File"
    
    try:
        # প্রতিটি ডিটেইলস আলাদা ভাবে লগ করা (বট শক্তিশালী করার জন্য)
        cleaned_filename = get_clean_filename(raw_name)
        v_quality = get_smart_quality(raw_name)
        a_audio = get_advanced_audio(raw_name)
        f_size = get_readable_size(file.file_size)

        # ফাইনাল ক্যাপশন ফরম্যাট করা
        final_caption = template.format(
            filename=cleaned_filename,
            quality=v_quality,
            audio=a_audio,
            size=f_size
        )
        
        # চ্যানেলে ক্যাপশন আপডেট
        await message.edit_caption(caption=final_caption)
        logger.info(f"Successfully Edited: {cleaned_filename} in Channel: {chat_id}")
        
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_caption(client, message)
    except Exception as e:
        logger.error(f"Failed to edit caption in {chat_id}: {e}")

# ==========================================
# ৬. বট এক্সিকিউশন
# ==========================================

if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে রান করা (Koyeb এর জন্য)
    logger.info("Starting Flask Web Server...")
    Thread(target=run_web).start()
    
    logger.info("🚀 Professional Auto-Caption Bot is Starting with Global Language Support...")
    app.run()
