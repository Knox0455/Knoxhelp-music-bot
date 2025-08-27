import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream
from yt_dlp import YoutubeDL

# 🔹 Configs
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "https://t.me/yourchannel")

# 🔹 Pyrogram Client
app = Client("music-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
pytg = PyTgCalls(app)

# 🔹 Song Queue
queues = {}

ydl_opts = {"format": "bestaudio"}

# 🔹 Start / Welcome
@app.on_message(filters.command("start"))
async def start(client, message):
    buttons = [
        [InlineKeyboardButton("📢 Support", url=SUPPORT_CHANNEL)],
        [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{(await app.get_me()).username}?startgroup=true")]
    ]
    text = f"""
👋 Hello {message.from_user.mention}!

🎶 I am a Telegram **Music Bot**  
Use /play <song name or link> to play music in VC.
"""
    await message.reply_animation(
        animation="https://media.giphy.com/media/3o7abKhOpu0NwenH3O/giphy.gif",
        caption=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# 🔹 Play Command
@app.on_message(filters.command("play"))
async def play(client, message):
    chat_id = message.chat.id
    if len(message.command) < 2:
        return await message.reply("❌ Please provide a song name or link!")

    query = " ".join(message.command[1:])
    await message.reply("🔎 Searching...")

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            url = info['url']
            title = info.get("title", "Unknown")
        except Exception as e:
            return await message.reply(f"❌ Error: {str(e)}")

    if chat_id not in queues:
        queues[chat_id] = []

    queues[chat_id].append({"title": title, "url": url})

    if len(queues[chat_id]) == 1:  # agar koi gaana play nhi ho raha
        await pytg.join_group_call(
            chat_id,
            InputAudioStream(url)
        )
        await message.reply(f"▶️ Playing: **{title}**")
    else:
        await message.reply(f"⏱ Added to queue: **{title}** (#{len(queues[chat_id])})")

if __name__ == "__main__":
    app.start()
    pytg.start()
    print("🚀 Music Bot Running...")
    app.idle()
from pytgcalls.types import Update

# 🔹 Skip Song
@app.on_message(filters.command("skip"))
async def skip(client, message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]:
        return await message.reply("❌ Queue is empty.")

    queues[chat_id].pop(0)  # current gaana hata do

    if queues[chat_id]:
        next_song = queues[chat_id][0]
        await pytg.change_stream(
            chat_id,
            InputAudioStream(next_song['url'])
        )
        await message.reply(f"⏭ Skipped! Now playing: **{next_song['title']}**")
    else:
        await pytg.leave_group_call(chat_id)
        await message.reply("✅ Queue finished. Left VC.")

# 🔹 Show Queue
@app.on_message(filters.command("queue"))
async def show_queue(client, message):
    chat_id = message.chat.id
    if chat_id not in queues or not queues[chat_id]:
        return await message.reply("🎶 Queue is empty.")
    
    text = "🎵 **Current Queue:**\n"
    for i, song in enumerate(queues[chat_id], start=1):
        text += f"{i}. {song['title']}\n"
    await message.reply(text)

# 🔹 Loop (toggle)
loop_enabled = {}

@app.on_message(filters.command("loop"))
async def loop_song(client, message):
    chat_id = message.chat.id
    if chat_id not in loop_enabled:
        loop_enabled[chat_id] = False

    loop_enabled[chat_id] = not loop_enabled[chat_id]
    status = "✅ Enabled" if loop_enabled[chat_id] else "❌ Disabled"
    await message.reply(f"🔁 Loop: {status}")

# 🔹 Stop / End
@app.on_message(filters.command("stop"))
async def stop(client, message):
    chat_id = message.chat.id
    if chat_id in queues:
        queues[chat_id] = []
    await pytg.leave_group_call(chat_id)
    await message.reply("🛑 Stopped & cleared queue.")
