import os
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient

# --- কনফিগারেশন ---
API_ID = int(os.environ.get("API_ID", "29462738"))
API_HASH = os.environ.get("API_HASH", "297f51aaab99720a09e80273628c3c24")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8673154872:AAHqVYxzUeJ2iAXdV8AGrDTPG0pDb2_UxAA")
MONGO_URL = os.environ.get("MONGO_URL", "DATABASE_URI ==== mongodb+srv://larib82632:larib82632@cluster0.rj7ed.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

# ডাটাবেস সেটআপ
db_client = AsyncIOMotorClient(MONGO_URL)
db = db_client["multi_caption_bot"]
cap_collection = db["channel_settings"]

app = Client("caption_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ডিফল্ট ক্যাপশন (যদি কোনো চ্যানেলে সেট করা না থাকে)
DEFAULT_CAPTION = """<b>{filename}</b>

💎 <b>Size:</b> {size}
🎧 <b>Audio:</b> {audio}"""

# অডিও ল্যাঙ্গুয়েজ ডিটেক্ট করার প্রফেশনাল লজিক
def get_audio_info(file_name):
    file_name = file_name.lower()
    audios = []
    if "hindi" in file_name: audios.append("Hindi")
    if "eng" in file_name: audios.append("English")
    if "bang" in file_name or "beng" in file_name: audios.append("Bangla")
    if "tam" in file_name: audios.append("Tamil")
    if "tel" in file_name: audios.append("Telugu")
    if "dual" in file_name: audios.append("Dual Audio")
    if "multi" in file_name: audios.append("Multi Audio")
    
    return " | ".join(audios) if audios else "Not Specified"

# ফাইল সাইজ ফরম্যাট
def humanbytes(size):
    if not size: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    await message.reply_text(
        f"হ্যালো {message.from_user.mention}!\n\nআমি একটি অ্যাডভান্স মাল্টি-চ্যানেল অটো ক্যাপশন বট।\n\n"
        "<b>কিভাবে সেটআপ করবেন?</b>\n"
        "১. আমাকে আপনার চ্যানেলে অ্যাডমিন করুন।\n"
        "২. আপনার চ্যানেল আইডি সংগ্রহ করুন (যেমন: -10012345678)\n"
        "৩. নিচের কমান্ডটি ব্যবহার করে ক্যাপশন সেট করুন:\n\n"
        "`/set_caption [চ্যানেল আইডি] [আপনার ক্যাপশন]`\n\n"
        "<b>ট্যাগগুলো:</b>\n"
        "{filename} - মুভির নাম\n"
        "{size} - সাইজ\n"
        "{audio} - অডিও ল্যাঙ্গুয়েজ\n\n"
        "উদাহরণ:\n`/set_caption -100123456 🎬 Movie: {filename} \n🎧 Audio: {audio} \n\n✅ Join: @MyChannel`"
    )

@app.on_message(filters.command("set_caption") & filters.private)
async def set_cap(client, message):
    if len(message.command) < 3:
        return await message.reply_text("❌ ভুল ফরম্যাট! \nব্যবহার: `/set_caption [Channel ID] [Caption]`")
    
    try:
        # কমান্ড থেকে আইডি এবং টেক্সট আলাদা করা
        channel_id = int(message.command[1])
        new_caption = message.text.split(None, 2)[2]
        
        await cap_collection.update_one(
            {"channel_id": channel_id},
            {"$set": {"caption_text": new_caption}},
            upsert=True
        )
        await message.reply_text(f"✅ চ্যানেল `{channel_id}` এর জন্য ক্যাপশন আপডেট হয়েছে!")
    except ValueError:
        await message.reply_text("❌ চ্যানেল আইডিটি সঠিক সংখ্যায় দিন (উদা: -100xxx)")

@app.on_message(filters.command("view_caption") & filters.private)
async def view_cap(client, message):
    if len(message.command) < 2:
        return await message.reply_text("ব্যবহার: `/view_caption [Channel ID]`")
    
    channel_id = int(message.command[1])
    data = await cap_collection.find_one({"channel_id": channel_id})
    
    if data:
        await message.reply_text(f"চ্যানেল: `{channel_id}`\nক্যাপশন:\n\n{data['caption_text']}")
    else:
        await message.reply_text("এই চ্যানেলের জন্য কোনো কাস্টম ক্যাপশন সেট করা নেই।")

@app.on_message(filters.channel & (filters.video | filters.document))
async def auto_caption(client, message):
    # চ্যানেলের আইডি নেওয়া
    chat_id = message.chat.id
    file = message.video or message.document
    if not file: return

    # ফাইল ইনফরমেশন প্রসেসিং
    file_name = file.file_name.replace(".", " ").replace("_", " ") if file.file_name else "Unknown"
    file_size = humanbytes(file.file_size)
    audio_info = get_audio_info(file_name)

    # ডাটাবেস থেকে ওই নির্দিষ্ট চ্যানেলের ক্যাপশন খোঁজা
    data = await cap_collection.find_one({"channel_id": chat_id})
    template = data["caption_text"] if data else DEFAULT_CAPTION

    # প্লেসহোল্ডারগুলো রিপ্লেস করা
    final_caption = template.format(
        filename=file_name,
        size=file_size,
        audio=audio_info
    )

    try:
        await message.edit_caption(final_caption)
    except Exception as e:
        print(f"Error in {chat_id}: {e}")

print("Professional Multi-Channel Bot Started...")
app.run()
