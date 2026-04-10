import os
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from flask import Flask
from threading import Thread

# --- লগিং সেটআপ ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- কনফিগারেশন ---
API_ID = int(os.environ.get("API_ID", "29462738"))
API_HASH = os.environ.get("API_HASH", "297f51aaab99720a09e80273628c3c24")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8673154872:AAHqVYxzUeJ2iAXdV8AGrDTPG0pDb2_UxAA")
# ডাটাবেস ইউআরএল থেকে অপ্রয়োজনীয় লেখা বাদ দিয়ে ক্লিন ইউআরএল
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://larib82632:larib82632@cluster0.rj7ed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# --- ডাটাবেস কানেকশন ---
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["Professional_Caption_Bot"]
cap_collection = db["channel_settings"]

# --- বট ক্লায়েন্ট ---
app = Client("caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ওয়েব সার্ভার (Koyeb Web Service এর জন্য) ---
# এটি কোয়েবকে বলবে যে বটটি সচল আছে
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Running Perfectly!"

def run_web():
    # কোয়েব ডিফল্ট পোর্ট ৮০৮০ ব্যবহার করে
    web_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- হেল্পার ফাংশনসমূহ ---

def get_audio_info(file_name):
    """ফাইলের নাম থেকে অডিও ল্যাঙ্গুয়েজ ডিটেক্ট করে"""
    file_name = file_name.lower()
    audios = []
    if any(x in file_name for x in ["hindi", "hin", "hnd"]): audios.append("Hindi")
    if any(x in file_name for x in ["english", "eng", "en"]): audios.append("English")
    if any(x in file_name for x in ["bangla", "bengali", "ben"]): audios.append("Bangla")
    if any(x in file_name for x in ["tamil", "tam"]): audios.append("Tamil")
    if any(x in file_name for x in ["telugu", "tel"]): audios.append("Telugu")
    if any(x in file_name for x in ["malayalam", "mal"]): audios.append("Malayalam")
    if any(x in file_name for x in ["kannada", "kan"]): audios.append("Kannada")
    if "dual" in file_name: audios.append("Dual Audio")
    if "multi" in file_name: audios.append("Multi Audio")
    
    return " | ".join(audios) if audios else "Not Specified"

def humanbytes(size):
    """বাইটকে সুন্দর ফরম্যাটে (MB/GB) রূপান্তর করে"""
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

def clean_filename(filename):
    """ফাইলের নাম থেকে এক্সটেনশন সরায় এবং ডট/আন্ডারস্কোর ক্লিন করে"""
    name, _ = os.path.splitext(filename)
    # ডট, আন্ডারস্কোর এবং ড্যাশ সরিয়ে স্পেস দেওয়া
    clean_name = name.replace(".", " ").replace("_", " ").replace("-", " ")
    # ডাবল স্পেস ক্লিন করা
    return " ".join(clean_name.split())

# --- বট কমান্ড হ্যান্ডলার ---

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    text = (
        f"👋 হ্যালো {message.from_user.mention}!\n\n"
        "আমি একটি প্রফেশনাল **মাল্টি-চ্যানেল অটো ক্যাপশন বট**।\n\n"
        "**কিভাবে ব্যবহার করবেন?**\n"
        "১. আমাকে আপনার চ্যানেলে অ্যাডমিন করুন।\n"
        "২. চ্যানেলের আইডি সংগ্রহ করুন।\n"
        "৩. নিচের ফরম্যাটে ক্যাপশন সেট করুন:\n\n"
        "`/set_caption -100xxxx [আপনার ক্যাপশন]`\n\n"
        "**ক্যাপশনে ব্যবহারযোগ্য ট্যাগ:**\n"
        "• `{filename}` - মুভির নাম\n"
        "• `{size}` - ফাইলের সাইজ\n"
        "• `{audio}` - অডিও ল্যাঙ্গুয়েজ\n\n"
        "**উদাহরণ:**\n"
        "`/set_caption -1001234567890 🎬 Movie: {filename}\n🔊 Audio: {audio}\n📁 Size: {size}\n\n✅ Join: @MyChannel`"
    )
    await message.reply_text(text)

@app.on_message(filters.command("set_caption") & filters.private)
async def set_caption_handler(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ **ভুল ফরম্যাট!**\n\nসঠিক নিয়ম: `/set_caption [Channel ID] [Caption Text]`")
    
    try:
        channel_id = int(message.command[1])
        caption_text = message.text.split(None, 2)[2]
        
        await cap_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"caption_text": caption_text}},
            upsert=True
        )
        await message.reply_text(f"✅ **সফল হয়েছে!**\n\nচ্যানেল আইডি `{channel_id}` এর জন্য ক্যাপশন সেট করা হয়েছে।")
    except ValueError:
        await message.reply_text("❌ চ্যানেল আইডিটি অবশ্যই একটি সংখ্যা হতে হবে (উদা: -100xxx)।")
    except Exception as e:
        await message.reply_text(f"❌ এরর: {e}")

@app.on_message(filters.command("view_caption") & filters.private)
async def view_caption_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("ব্যবহার: `/view_caption [Channel ID]`")
    
    try:
        channel_id = int(message.command[1])
        data = await cap_collection.find_one({"channel_id": channel_id})
        if data:
            await message.reply_text(f"**চ্যানেল আইডি:** `{channel_id}`\n\n**বর্তমান ক্যাপশন:**\n\n{data['caption_text']}")
        else:
            await message.reply_text("⚠️ এই চ্যানেলের জন্য কোনো কাস্টম ক্যাপশন সেট করা নেই।")
    except Exception as e:
        await message.reply_text(f"❌ এরর: {e}")

# --- অটো ক্যাপশন লজিক (চ্যানেলের জন্য) ---

@app.on_message(filters.channel & (filters.video | filters.document))
async def auto_caption_handler(client, message):
    chat_id = message.chat.id
    file = message.video or message.document
    
    # ফাইল না থাকলে বা মেসেজ এডিট করা সম্ভব না হলে ফিরে যাও
    if not file: return

    # ডাটাবেস থেকে ক্যাপশন ফরম্যাট সংগ্রহ
    data = await cap_collection.find_one({"channel_id": chat_id})
    if not data:
        # কোনো ক্যাপশন সেট করা না থাকলে ডিফল্ট ফরম্যাট ব্যবহার হবে
        template = "🎬 **Name:** {filename}\n\n🔊 **Audio:** {audio}\n📁 **Size:** {size}"
    else:
        template = data["caption_text"]

    # ফাইল ইনফরমেশন প্রসেসিং
    raw_file_name = file.file_name if file.file_name else "Unknown"
    clean_name = clean_filename(raw_file_name)
    file_size = humanbytes(file.file_size)
    audio_info = get_audio_info(raw_file_name)

    # প্লেসহোল্ডারগুলো পূরণ করা
    final_caption = template.format(
        filename=clean_name,
        size=file_size,
        audio=audio_info
    )

    try:
        await message.edit_caption(caption=final_caption)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await message.edit_caption(caption=final_caption)
    except Exception as e:
        logger.error(f"Error in channel {chat_id}: {e}")

# --- বট রান করা ---

if __name__ == "__main__":
    # ওয়েব সার্ভার আলাদা থ্রেডে চালানো যাতে কোয়েব সচল থাকে
    Thread(target=run_web).start()
    
    logger.info("Bot is starting...")
    app.run()
