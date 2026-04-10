import os
import re
import asyncio
import logging
import time
from threading import Thread
from datetime import datetime, timedelta
from flask import Flask
from pyrogram import Client, filters, errors, idle
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
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8297458824")) # এখানে আপনার নিজের আইডি দিন

# ==========================================
# ৩. ডাটাবেস ও ওয়েব সার্ভার কানেকশন
# ==========================================
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Final_AutoCaption_Pro"]
cap_collection = db["channel_configs"]
premium_collection = db["premium_users"]

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "🔥 Bot is Online and Healthy! Powered by Flask System."

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ==========================================
# ৪. স্মার্ট এক্সট্রাকশন ইউটিলিটি (Detailed Brain - হুবহু আগের মতো)
# ==========================================

def get_clean_filename(file_name):
    """মুভি এবং ওয়েব সিরিজের নাম ক্লিন করা (এপিসোড রেঞ্জ সাপোর্ট সহ)"""
    name, ext = os.path.splitext(file_name)
    name = name.replace(".", " ").replace("_", " ").replace("-", " ")
    
    season_pattern = r'([sS]eason\s?\d+|[sS]\d+)'
    episode_pattern = r'(\[?[eE](pisode|p)?\s?\d+[\s\-\~\&to]*\d+\]?)'
    year_pattern = r'(19|20)\d{2}'

    found_season = re.search(season_pattern, name, re.IGNORECASE)
    found_episode = re.search(episode_pattern, name, re.IGNORECASE)
    found_year = re.search(year_pattern, name)

    clean_name = name
    info_tag = ""

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
    elif found_year:
        year_idx = found_year.start()
        clean_name = name[:year_idx]
        info_tag = found_year.group(0)

    # জঞ্জাল শব্দ রিমুভ করার বিশাল লিস্ট (আপনার দেয়া সম্পূর্ণ লিস্ট)
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
    """দুনিয়ার সব ল্যাঙ্গুয়েজ ডিটেক্ট করার জন্য আপনার দেয়া সেই বিশাল লজিক"""
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
    
    # ২. ইন্টারন্যাশনাল
    if any(x in n for x in ['english', 'eng', 'en']): a.append("English")
    if any(x in n for x in ['spanish', 'spa', 'esp']): a.append("Spanish")
    if any(x in n for x in ['french', 'fre', 'fra']): a.append("French")
    if any(x in n for x in ['russian', 'rus']): a.append("Russian")
    if any(x in n for x in ['german', 'ger', 'deu']): a.append("German")
    if any(x in n for x in ['italian', 'ita']): a.append("Italian")
    if any(x in n for x in ['portuguese', 'por']): a.append("Portuguese")
    
    # ৩. ইস্ট এশিয়ান
    if any(x in n for x in ['korean', 'kor', 'k-drama']): a.append("Korean")
    if any(x in n for x in ['japanese', 'jap', 'anime']): a.append("Japanese")
    if any(x in n for x in ['chinese', 'chi']): a.append("Chinese")
    if any(x in n for x in ['thai', 'tha']): a.append("Thai")
    
    # ৪. মিডল ইস্ট
    if any(x in n for x in ['arabic', 'ara']): a.append("Arabic")
    if any(x in n for x in ['turkish', 'tur']): a.append("Turkish")
    
    is_dual = any(x in n for x in ['dual', '2-audio', 'd-audio'])
    is_multi = any(x in n for x in ['multi', 'm-audio', 'auds'])
    
    if a:
        unique_audio = list(set(a))
        res = " | ".join(unique_audio)
        if len(unique_audio) >= 3:
            return f"Multi Audio [{res}]"
        return res
    
    if is_multi: return "Multi Audio"
    if is_dual: return "Dual Audio (Hindi-English)"
    return "Hindi"

def get_readable_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024

# ==========================================
# ৫. প্রিমিয়াম ম্যানেজমেন্ট সিস্টেম (নতুন লজিক)
# ==========================================

async def auto_expiry_checker(client):
    """মেয়াদ শেষ হওয়া ইউজারদের অটো কিক করার ব্যাকগ্রাউন্ড টাস্ক"""
    while True:
        try:
            now = datetime.utcnow()
            expired_users = premium_collection.find({"expiry_date": {"$lt": now}})
            
            async for user in expired_users:
                u_id = user["user_id"]
                c_id = user["channel_id"]
                try:
                    await client.ban_chat_member(c_id, u_id)
                    await asyncio.sleep(1)
                    await client.unban_chat_member(c_id, u_id) # কিক করে আনব্যান যাতে সে আর মেম্বার না থাকে
                    
                    await premium_collection.delete_one({"_id": user["_id"]})
                    await client.send_message(u_id, "⚠️ আপনার প্রিমিয়াম সাবস্ক্রিপশন শেষ হয়ে গেছে এবং আপনাকে চ্যানেল থেকে রিমুভ করা হয়েছে।")
                    logger.info(f"Kicked expired user {u_id}")
                except Exception as e:
                    logger.error(f"Error kicking {u_id}: {e}")
        except Exception as e:
            logger.error(f"Checker Error: {e}")
        await asyncio.sleep(3600) # প্রতি ১ ঘণ্টা পর চেক করবে

# ==========================================
# ৬. টেলিগ্রাম বট হ্যান্ডলার
# ==========================================
app = Client("smart_caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    start_text = (
        f"👋 **হ্যালো {message.from_user.mention}!**\n\n"
        "আমি একটি অ্যাডভান্সড অটো ক্যাপশন এবং প্রিমিয়াম মেম্বারশিপ ম্যানেজার বট।\n\n"
        "🚀 **কমান্ডসমূহ:**\n"
        "• `/set_caption` - ক্যাপশন সেট করা\n"
        "• `/add_premium` - ইউজার অ্যাড করা (Admin Only)\n"
        "• `/my_plan` - নিজের প্ল্যান দেখা"
    )
    await message.reply_text(start_text)

@app.on_message(filters.command("add_premium") & filters.user(ADMIN_ID))
async def add_premium_handler(client, message):
    if len(message.command) < 4:
        return await message.reply_text("❌ **ব্যবহার:** `/add_premium [User_ID] [Channel_ID] [Days]`")
    
    try:
        user_id = int(message.command[1])
        channel_id = int(message.command[2])
        days = int(message.command[3])
        
        expiry_date = datetime.utcnow() + timedelta(days=days)
        await premium_collection.update_one(
            {"user_id": user_id, "channel_id": channel_id},
            {"$set": {"expiry_date": expiry_date}},
            upsert=True
        )
        await message.reply_text(f"✅ ইউজার `{user_id}` কে {days} দিনের জন্য অ্যাড করা হয়েছে।\nমেয়াদ শেষ: {expiry_date.strftime('%Y-%m-%d')}")
        await client.send_message(user_id, f"🎉 অভিনন্দন! আপনাকে {days} দিনের জন্য প্রিমিয়াম চ্যানেলে এক্সেস দেওয়া হয়েছে।")
    except Exception as e:
        await message.reply_text(f"⚠️ এরর: {e}")

@app.on_message(filters.command("my_plan") & filters.private)
async def my_plan_handler(client, message):
    data = await premium_collection.find_one({"user_id": message.from_user.id})
    if data:
        expiry = data["expiry_date"]
        remaining = expiry - datetime.utcnow()
        await message.reply_text(f"🌟 **আপনার প্ল্যান:**\n⏳ বাকি আছে: {remaining.days} দিন\n📅 শেষ হবে: {expiry.strftime('%Y-%m-%d')}")
    else:
        await message.reply_text("❌ আপনার কোনো একটিভ প্রিমিয়াম প্ল্যান নেই।")

@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ **ব্যবহার:** `/set_caption [Channel ID] [Caption]`")
    try:
        channel_id = int(message.command[1])
        caption_text = message.text.split(None, 2)[2]
        await cap_collection.update_one({"channel_id": channel_id}, {"$set": {"caption_text": caption_text}}, upsert=True)
        await message.reply_text(f"✅ চ্যানেল `{channel_id}` এর ক্যাপশন সেট করা হয়েছে।")
    except Exception as e:
        await message.reply_text(f"⚠️ এরর: {e}")

@app.on_message(filters.channel & (filters.video | filters.document))
async def auto_caption(client, message):
    chat_id = message.chat.id
    file = message.video or message.document
    if not file: return

    config = await cap_collection.find_one({"channel_id": chat_id})
    template = config["caption_text"] if config else "🎬 **Name:** {filename}\n🌟 **Quality:** {quality}\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"

    raw_name = file.file_name if file.file_name else "Unknown File"
    
    try:
        final_caption = template.format(
            filename=get_clean_filename(raw_name),
            quality=get_smart_quality(raw_name),
            audio=get_advanced_audio(raw_name),
            size=get_readable_size(file.file_size)
        )
        await message.edit_caption(caption=final_caption)
    except errors.FloodWait as e:
        await asyncio.sleep(e.value)
        await auto_caption(client, message)
    except Exception as e:
        logger.error(f"Failed in {chat_id}: {e}")

# ==========================================
# ৭. মেইন এক্সিকিউশন
# ==========================================

async def main():
    # ওয়েব সার্ভার
    Thread(target=run_web, daemon=True).start()
    
    # বট স্টার্ট
    await app.start()
    logger.info("🚀 Bot is Running with Premium Manager...")
    
    # অটো-কিক টাস্ক রান করা
    asyncio.create_task(auto_expiry_checker(app))
    
    await idle()
    await app.stop()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
