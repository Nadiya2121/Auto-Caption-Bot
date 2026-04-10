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
# আপনার দেওয়া তথ্যগুলো হুবহু রাখা হয়েছে
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
# ৪. স্মার্ট এক্সট্রাকশন ইউটিলিটি (The Brain - Updated for Web Series)
# ==========================================

def get_clean_filename(file_name):
    """মুভি এবং ওয়েব সিরিজের নাম স্মার্টলি ক্লিন করা এবং এপিসোড রেঞ্জ খুঁজে বের করা"""
    # এক্সটেনশন বাদ দেওয়া
    name, _ = os.path.splitext(file_name)
    
    # ডট, আন্ডারস্কোর এবং ড্যাশ সরিয়ে স্পেস দেওয়া
    name = re.sub(r'[\.\_\-]', ' ', name)
    
    # প্যাটার্ন ১: সিজন (S01, Season 01, S1)
    season_pattern = r'([sS]eason\s?\d+|[sS]\d+)'
    
    # প্যাটার্ন ২: এপিসোড (E01, Ep 01, Episode 01, এবং রেঞ্জ যেমন 01-10, 01 to 05)
    episode_pattern = r'([eE]pisode|[eE]p|[eE])?\s?\d+\s?([-–—to\s]+\d+)?'
    
    # প্যাটার্ন ৩: মুভির সাল
    year_match = re.search(r'(19|20)\d{2}', name)
    
    found_season = re.search(season_pattern, name, re.IGNORECASE)
    found_episode = re.search(episode_pattern, name, re.IGNORECASE)
    
    clean_title = name
    extra_tag = ""

    # ওয়েব সিরিজ ডিটেকশন লজিক
    if found_season or (found_episode and not year_match):
        # সিজন থাকলে সেটি নিন
        s_txt = found_season.group(0).upper() if found_season else ""
        
        # এপিসোড বা রেঞ্জ থাকলে সেটি নিন
        e_txt = ""
        if found_episode:
            # টেক্সট থেকে এপিসোড রেঞ্জ বের করার জন্য সব ম্যাচ চেক করা
            all_eps = [m.group(0) for m in re.finditer(episode_pattern, name, re.IGNORECASE)]
            for ep in all_eps:
                if any(char.isdigit() for char in ep):
                    e_txt = ep.upper()
                    break
        
        # টাইটেল থেকে সিজন/এপিসোড যেখানে শুরু হয়েছে তার পরের অংশ কেটে ফেলা
        cut_idx = len(name)
        if found_season: cut_idx = min(cut_idx, found_season.start())
        if found_episode: cut_idx = min(cut_idx, found_episode.start())
        
        clean_title = name[:cut_idx]
        extra_tag = f"{s_txt} {e_txt}".strip()
        
    elif year_match:
        # এটি মুভি (সালের পরের অংশ কাটা)
        year_idx = year_match.start()
        clean_title = name[:year_idx]
        extra_tag = year_match.group(0)

    # জঞ্জাল শব্দ রিমুভ করা (টাইটেল অংশ থেকে)
    junk_words = [
        '720p', '1080p', '480p', '2160p', '4k', 'hevc', 'h264', 'h265', 'x264', 'x265',
        '10bit', 'web-dl', 'webdl', 'bluray', 'hdrip', 'brrip', 'nf', 'web', 'dl', 'aac',
        'esub', 'sub', 'dual', 'multi', 'hdtv', 'proper', 'repack', 'hindi', 'english', 'org'
    ]
    
    for word in junk_words:
        clean_title = re.sub(rf'\b{word}\b', '', clean_title, flags=re.IGNORECASE)
    
    # ফাইনাল ক্লিনআপ
    final_title = ' '.join(clean_title.split())
    return f"{final_title} {extra_tag}".strip() if extra_tag else final_title

def get_smart_quality(name):
    """ফাইলের নাম থেকে ভিডিও কোয়ালিটি খুঁজে বের করা"""
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
    """ফাইলের নাম থেকে অত্যন্ত স্মার্টলি অডিও ডিটেক্ট করা"""
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
        if "dual" in name: return "Dual Audio (Hindi-English)"
        if "multi" in name: return "Multi Audio"
        return "Hindi"
    
    return " | ".join(audios)

def get_readable_size(size):
    """বাইটকে MB/GB তে রূপান্তর"""
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
    start_text = (
        f"👋 **হ্যালো {message.from_user.mention}!**\n\n"
        "আমি একটি অ্যাডভান্সড **মাল্টি-চ্যানেল অটো ক্যাপশন বট**।\n\n"
        "✅ **আমি এখন মুভি এবং ওয়েব সিরিজ (এপিসোড রেঞ্জ সহ) স্মার্টলি ক্লিন করতে পারি!**\n\n"
        "🚀 **কিভাবে ব্যবহার করবেন?**\n"
        "১. আপনার চ্যানেলে আমাকে অ্যাডমিন করুন।\n"
        "২. নিচের কমান্ড দিয়ে ক্যাপশন সেট করুন:\n\n"
        "`/set_caption [Channel_ID] [Your_Caption]`\n\n"
        "📑 **ট্যাগসমূহ:** `{filename}`, `{quality}`, `{audio}`, `{size}`"
    )
    await message.reply_text(start_text)

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
        await message.reply_text(f"✅ **সফল হয়েছে!**\nচ্যানেল `{channel_id}` এর জন্য ক্যাপশন সেট করা হয়েছে।")
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
        template = "🎬 **Name:** {filename}\n🌟 **Quality:** {quality}\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"

    raw_name = file.file_name if file.file_name else "Unknown"
    
    try:
        # স্মার্ট ডেটা প্রসেসিং
        final_caption = template.format(
            filename=get_clean_filename(raw_name),
            quality=get_smart_quality(raw_name),
            audio=get_advanced_audio(raw_name),
            size=get_readable_size(file.file_size)
        )
        
        # ক্যাপশন আপডেট
        await message.edit_caption(caption=final_caption)
        logger.info(f"Updated caption in: {chat_id}")
        
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_caption(client, message)
    except Exception as e:
        logger.error(f"Error in {chat_id}: {e}")

# ==========================================
# ৬. বট এক্সিকিউশন
# ==========================================

if __name__ == "__main__":
    # Flask সার্ভার আলাদা থ্রেডে রান করা
    Thread(target=run_web).start()
    
    logger.info("🚀 Smart Auto-Caption Bot is Starting...")
    app.run()
