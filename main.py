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

# ==========================================================
# ১. লগিং এবং কনফিগারেশন সেটআপ
# ==========================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# এনভায়রনমেন্ট ভেরিয়েবল থেকে ডেটা নেওয়া
API_ID = int(os.environ.get("API_ID", "29462738"))
API_HASH = os.environ.get("API_HASH", "297f51aaab99720a09e80273628c3c24")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8673154872:AAHqVYxzUeJ2iAXdV8AGrDTPG0pDb2_UxAA")
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://larib82632:larib82632@cluster0.rj7ed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ==========================================================
# ২. ডাটাবেস এবং ওয়েব সার্ভার (Koyeb এর জন্য)
# ==========================================================
try:
    db_client = AsyncIOMotorClient(MONGO_URL)
    db = db_client["Smart_AutoCaption_DB"]
    cap_collection = db["channel_settings"]
    logger.info("✅ MongoDB Connected Successfully!")
except Exception as e:
    logger.error(f"❌ MongoDB Connection Error: {e}")

# Koyeb Web Service সচল রাখার জন্য Flask
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running and Healthy!"

def run_web():
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# ==========================================================
# ৩. স্মার্ট ইনফরমেশন এক্সট্রাকশন (The "Brain")
# ==========================================================

def get_clean_name(file_name):
    """মুভির নাম থেকে জঞ্জাল পরিষ্কার করার স্মার্ট লজিক"""
    # এক্সটেনশন বাদ দেওয়া
    name = os.path.splitext(file_name)[0]
    
    # অপ্রয়োজনীয় ডট, আন্ডারস্কোর সরিয়ে স্পেস দেওয়া
    name = re.sub(r'[\.\_\-]', ' ', name)
    
    # যদি নামে সাল থাকে (যেমন 2024, 2026), তবে সালের পরের অংশটুকু কেটে ফেলা
    year_match = re.search(r'(19|20)\d{2}', name)
    if year_match:
        year_index = year_match.end()
        name = name[:year_index]
    
    # কিছু কমন জঞ্জাল শব্দ রিমুভ করা
    junk_words = [
        '720p', '1080p', '480p', '2160p', '4k', 'hevc', 'h264', 'h265', 'x264', 'x265',
        '10bit', 'web-dl', 'webdl', 'bluray', 'hdrip', 'brrip', 'nf', 'web', 'dl', 'aac',
        'the punisher', 'esub', 'sub', 'dual', 'multi'
    ]
    
    for word in junk_words:
        name = re.sub(rf'\b{word}\b', '', name, flags=re.IGNORECASE)
    
    # অতিরিক্ত স্পেস ক্লিন করা
    clean_name = ' '.join(name.split())
    return clean_name if clean_name else file_name

def get_smart_audio(file_name):
    """ফাইলের নাম না থাকলেও স্মার্টলি অডিও ডিটেক্ট করা"""
    name = file_name.lower()
    audios = []
    
    # সরাসরি নাম চেক
    if any(x in name for x in ['hindi', 'hin', 'hnd']): audios.append("Hindi")
    if any(x in name for x in ['english', 'eng', 'en']): audios.append("English")
    if any(x in name for x in ['bangla', 'ben', 'bd']): audios.append("Bangla")
    if any(x in name for x in ['tamil', 'tam']): audios.append("Tamil")
    if any(x in name for x in ['telugu', 'tel']): audios.append("Telugu")
    
    # স্মার্ট ডিটেকশন (যদি নাম না থাকে কিন্তু সোর্স থাকে)
    if not audios:
        if "nf" in name or "web" in name:
            return "Hindi | English (Smart Detect)"
        if "dual" in name:
            return "Dual Audio (Hindi-English)"
        return "Hindi (Default)"
    
    return " | ".join(audios)

def get_readable_size(size):
    """বাইটকে MB/GB তে রূপান্তর"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

# ==========================================================
# ৪. টেলিগ্রাম বট হ্যান্ডলারসমূহ
# ==========================================================
app = Client("smart_caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    text = (
        f"👋 **স্বাগতম {message.from_user.mention}!**\n\n"
        "আমি একটি **অ্যাডভান্সড অটো-ক্যাপশন বট**। মুভি চ্যানেলের জন্য আমাকে ডিজাইন করা হয়েছে।\n\n"
        "✨ **আমার বৈশিষ্ট্য:**\n"
        "• মাল্টি-চ্যানেল সাপোর্ট (প্রতি চ্যানেলে আলাদা ক্যাপশন)।\n"
        "• স্মার্ট মুভি নাম ক্লিনার।\n"
        "• অটো অডিও ল্যাঙ্গুয়েজ ডিটেকশন।\n"
        "• সম্পূর্ণ কাস্টম ক্যাপশন ফরম্যাট।\n\n"
        "🚀 **কিভাবে সেটআপ করবেন?**\n"
        "১. আপনার চ্যানেলে আমাকে অ্যাডমিন করুন।\n"
        "২. বটের ইনবক্সে লিখুন: `/set_caption [Channel ID] [Caption]`"
    )
    buttons = [[
        InlineKeyboardButton("📢 Update Channel", url="https://t.me/YourChannel"),
        InlineKeyboardButton("🛠 Help", callback_data="help_data")
    ]]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption_cmd(client, message):
    if len(message.command) < 3:
        usage = (
            "❌ **ভুল ফরম্যাট!**\n\n"
            "সঠিক নিয়ম: `/set_caption -100xxxxxxxx [ক্যাপশন]`\n\n"
            "**ট্যাগসমূহ:**\n"
            "• `{filename}` - ক্লিন করা মুভির নাম\n"
            "• `{size}` - ফাইলের সাইজ\n"
            "• `{audio}` - অডিও ল্যাঙ্গুয়েজ\n\n"
            "**উদাহরণ:**\n"
            "`/set_caption -1001234 🎬 মুভি: {filename} \n🔊 অডিও: {audio} \n📁 সাইজ: {size}`"
        )
        return await message.reply_text(usage)
    
    try:
        channel_id = int(message.command[1])
        new_caption = message.text.split(None, 2)[2]
        
        await cap_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"caption": new_caption}},
            upsert=True
        )
        await message.reply_text(f"✅ **সফল!**\nচ্যানেল `{channel_id}` এর জন্য ক্যাপশন আপডেট হয়েছে।")
    except Exception as e:
        await message.reply_text(f"⚠️ এরর: {e}")

@app.on_message(filters.command("view_caption") & filters.private)
async def view_caption_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply_text("ব্যবহার: `/view_caption [Channel ID]`")
    
    channel_id = int(message.command[1])
    data = await cap_collection.find_one({"channel_id": channel_id})
    
    if data:
        await message.reply_text(f"📌 **আপনার বর্তমান ক্যাপশন:**\n\n`{data['caption']}`")
    else:
        await message.reply_text("❌ এই চ্যানেলের জন্য কোনো ক্যাপশন সেট করা নেই।")

# ==========================================================
# ৫. মূল কাজ: অটো ক্যাপশন এডিটিং (চ্যানেল পার্ট)
# ==========================================================

@app.on_message(filters.channel & (filters.video | filters.document))
async def auto_caption_handler(client, message):
    try:
        chat_id = message.chat.id
        file = message.video or message.document
        if not file:
            return

        # ডাটাবেস থেকে ওই চ্যানেলের কাস্টম ক্যাপশন আনা
        channel_data = await cap_collection.find_one({"channel_id": chat_id})
        if not channel_data:
            # যদি কোনো ক্যাপশন সেট না থাকে, তবে ডিফল্ট
            template = "🎬 **Name:** {filename}\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"
        else:
            template = channel_data["caption"]

        # স্মার্ট তথ্য প্রসেসিং
        raw_name = file.file_name if file.file_name else "Unknown_File"
        clean_name = get_clean_name(raw_name)
        audio_info = get_smart_audio(raw_name)
        file_size = get_readable_size(file.file_size)

        # প্লেসহোল্ডার পূরণ
        final_caption = template.format(
            filename=clean_name,
            size=file_size,
            audio=audio_info
        )

        # ক্যাপশন এডিট করা
        await message.edit_caption(caption=final_caption)
        logger.info(f"✅ Success: Caption updated in {chat_id}")

    except errors.FloodWait as e:
        logger.warning(f"⚠️ FloodWait: Waiting for {e.value} seconds")
        await asyncio.sleep(e.value)
        await auto_caption_handler(client, message)
    except Exception as e:
        logger.error(f"❌ Error in channel {chat_id}: {e}")

# ==========================================================
# ৬. বট রান করা
# ==========================================================

if __name__ == "__main__":
    # ওয়েব সার্ভার আলাদা থ্রেডে চালানো (Koyeb এর জন্য)
    Thread(target=run_web).start()
    
    logger.info("🚀 Bot is Starting...")
    app.run()
