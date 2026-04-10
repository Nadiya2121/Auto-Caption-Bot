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
# ১. প্রফেশনাল লগিং সেটআপ (অরিজিনাল)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# ২. কনফিগারেশন (Environment Variables - অরিজিনাল)
# ==========================================
API_ID = int(os.environ.get("API_ID", "29462738"))
API_HASH = os.environ.get("API_HASH", "297f51aaab99720a09e80273628c3c24")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8673154872:AAHqVYxzUeJ2iAXdV8AGrDTPG0pDb2_UxAA")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://larib82632:larib82632@cluster0.rj7ed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ==========================================
# ৩. ডাটাবেস ও ওয়েব সার্ভার কানেকশন (অরিজিনাল)
# ==========================================
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Final_AutoCaption_Pro"]
cap_collection = db["channel_configs"]

# Koyeb Web Service সচল রাখার জন্য Flask Server
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🔥 Bot is Online and Healthy! Powered by Flask."

def run_web():
    # Koyeb এর ডিফল্ট পোর্ট ৮০৮০ ব্যবহার করবে
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ৪. স্মার্ট এক্সট্রাকশন ইউটিলিটি (The Brain - Full Detailed Version)
# ==========================================

def get_clean_filename(file_name):
    """মুভি এবং ওয়েব সিরিজের নাম স্মার্টলি ক্লিন করা (এপিসোড রেঞ্জ E11-20 সহ)"""
    # ১. এক্সটেনশন আলাদা করা
    name, ext = os.path.splitext(file_name)
    
    # ২. ডট, আন্ডারস্কোর এবং ড্যাশ সরিয়ে স্পেস দেওয়া
    name = re.sub(r'[\.\_\-]', ' ', name)
    
    # ৩. প্যাটার্ন ডিটেকশন (Season & Episode Range)
    # এটি S01, Season 1, [E11-20], Ep 01-10 ইত্যাদি ডিটেক্ট করবে
    season_pattern = r'([sS]eason\s?\d+|[sS]\d+)'
    # এপিসোড প্যাটার্নটি ব্র্যাকেট এবং ড্যাশসহ রেঞ্জ ডিটেক্ট করার জন্য আপডেট করা হয়েছে
    episode_pattern = r'(\[?[eE]pisode\s?\d+.*?\]?|\[?[eE]p\s?\d+.*?\]?|\[?[eE]\d+.*?\]?)'
    year_pattern = r'(19|20)\d{2}'

    found_season = re.search(season_pattern, name, re.IGNORECASE)
    found_episode = re.search(episode_pattern, name, re.IGNORECASE)
    found_year = re.search(year_pattern, name)

    clean_name = name
    info_tag = ""

    # ওয়েব সিরিজ লজিক (যদি সিজন বা এপিসোড থাকে)
    if found_season or found_episode:
        cut_idx = len(name)
        if found_season:
            cut_idx = min(cut_idx, found_season.start())
            info_tag += " " + found_season.group(0).upper()
        if found_episode:
            cut_idx = min(cut_idx, found_episode.start())
            # এপিসোড টেক্সট ক্লিন করা (যেমন: [E11-20] থেকে E11-20)
            ep_text = found_episode.group(0).upper().replace('[', '').replace(']', '').strip()
            info_tag += f" [{ep_text}]"
        
        clean_name = name[:cut_idx]
    
    # মুভি লজিক (যদি শুধু সাল থাকে)
    elif found_year:
        year_idx = found_year.start()
        clean_name = name[:year_idx]
        info_tag = found_year.group(0)

    # ৪. জঞ্জাল শব্দ রিমুভ করা (অরিজিনাল লিস্ট + অতিরিক্ত)
    junk_words = [
        '720p', '1080p', '480p', '2160p', '4k', 'hevc', 'h264', 'h265', 'x264', 'x265',
        '10bit', 'web-dl', 'webdl', 'bluray', 'hdrip', 'brrip', 'nf', 'web', 'dl', 'aac',
        'the punisher', 'esub', 'sub', 'dual', 'multi', 'hdtv', 'proper', 'repack', 
        'combined', 'swapnonil', 'kmhd'
    ]
    
    for word in junk_words:
        clean_name = re.sub(rf'\b{word}\b', '', clean_name, flags=re.IGNORECASE)
    
    # ৫. অতিরিক্ত স্পেস ক্লিন করা
    final_title = ' '.join(clean_name.split())
    return f"{final_title} {info_tag.strip()}".strip() if info_tag else final_title

def get_smart_quality(name):
    """ফাইলের নাম থেকে ভিডিও কোয়ালিটি খুঁজে বের করা (অরিজিনাল)"""
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
    """অরিজিনাল মাল্টি-ল্যাঙ্গুয়েজ অডিও ডিটেকশন"""
    name = file_name.lower()
    audios = []
    
    if any(x in name for x in ['hindi', 'hin', 'hnd']): audios.append("Hindi")
    if any(x in name for x in ['english', 'eng', 'en']): audios.append("English")
    if any(x in name for x in ['bangla', 'ben', 'bd']): audios.append("Bangla")
    if any(x in name for x in ['tamil', 'tam']): audios.append("Tamil")
    if any(x in name for x in ['telugu', 'tel']): audios.append("Telugu")
    if any(x in name for x in ['kannada', 'kan']): audios.append("Kannada")
    if any(x in name for x in ['malayalam', 'mal']): audios.append("Malayalam")
    
    if not audios:
        if "dual" in name: return "Dual Audio"
        if "multi" in name: return "Multi Audio"
        return "Hindi" 
    
    return " | ".join(audios)

def get_readable_size(size):
    """অরিজিনাল সাইজ কনভার্টার"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# ==========================================
# ৫. টেলিগ্রাম বট ফাংশনালিটি (অরিজিনাল ফিচারস)
# ==========================================
app = Client("smart_caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    # অরিজিনাল প্রফেশনাল এক্সাম্পল টেক্সট
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
        "• `{filename}` - ক্লিন মুভি/সিরিজ নাম (E11-20 সাপোর্ট সহ)\n"
        "• `{quality}` - ভিডিও কোয়ালিটি\n"
        "• `{audio}` - অডিও ল্যাঙ্গুয়েজ\n"
        "• `{size}` - ফাইলের সাইজ\n\n"
        "💡 **নিচের উদাহরণটি দেখে আইডি পরিবর্তন করে ব্যবহার করুন:**"
    )
    
    await message.reply_text(start_text)
    await asyncio.sleep(1)
    await message.reply_text(f"**উদাহরণ ফরম্যাট:**\n\n`/set_caption -100xxxxxxxx {example}`")

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

    # ডাটাবেস থেকে ক্যাপশন চেক
    config = await cap_collection.find_one({"channel_id": chat_id})
    if config:
        template = config["caption_text"]
    else:
        # ডিফল্ট ক্যাপশন
        template = "🎬 **Name:** {filename}\n🌟 **Quality:** {quality}\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"

    raw_name = file.file_name if file.file_name else "Unknown"
    
    try:
        # স্মার্ট ডেটা প্রসেসিং (উইথ সিরিজ সাপোর্ট)
        processed_filename = get_clean_filename(raw_name)
        processed_quality = get_smart_quality(raw_name)
        processed_audio = get_advanced_audio(raw_name)
        processed_size = get_readable_size(file.file_size)

        final_caption = template.format(
            filename=processed_filename,
            quality=processed_quality,
            audio=processed_audio,
            size=processed_size
        )
        
        # ক্যাপশন আপডেট (অরিজিনাল ফ্লাডওয়েট হ্যান্ডলিং সহ)
        await message.edit_caption(caption=final_caption)
        logger.info(f"Updated caption in channel: {chat_id}")
        
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_caption(client, message)
    except Exception as e:
        logger.error(f"Error in {chat_id}: {e}")

# ==========================================
# ৬. বট এক্সিকিউশন (অরিজিনাল থ্রেড সিস্টেম)
# ==========================================

if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে রান করা
    Thread(target=run_web).start()
    
    logger.info("🚀 Professional Auto-Caption Bot is Starting (Full Version)...")
    app.run()
