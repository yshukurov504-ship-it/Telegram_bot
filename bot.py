import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    CallbackQueryHandler,
    filters,
)
import yt_dlp

# 🔑 Bot token
TOKEN = '7763441253:AAHZLZSYrFVDavcQPMbsl4FLeYZJRPTrsIY'

formats = ["144", "240", "360", "480", "720", "1080"]
user_data = {}

# 📢 Reklama funksiyasi
async def send_reklama(chat_id, context):
    try:
        with open("reklama/matn.txt", "r", encoding="utf-8") as f:
            matn = f.read().strip()

        keyboard = None
        tugma_path = "reklama/tugma.txt"
        if os.path.exists(tugma_path):
            with open(tugma_path, "r", encoding="utf-8") as f:
                tugma_yozuv, tugma_url = f.read().strip().split("|")
                button = InlineKeyboardButton(tugma_yozuv, url=tugma_url)
                keyboard = InlineKeyboardMarkup([[button]])

        await context.bot.send_message(chat_id=chat_id, text=matn, reply_markup=keyboard)
    except Exception as e:
        print("❌ Reklama xatosi:", e)

# 🔘 Boshlang‘ich tugmalar: Audio va Video
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 Audio", callback_data="audio")],
        [InlineKeyboardButton("🎥 Video", callback_data="video_menu")]
    ])

# 🎞️ Sifat tanlash tugmalari
def quality_buttons():
    return InlineKeyboardMarkup([
        *[[InlineKeyboardButton(f"{f}p", callback_data=f)] for f in formats]
    ])

# 🚪 /start komandasi
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("🎥 Video linkni yuboring:")
    await send_reklama(update.effective_chat.id, context)

# 🔗 Link qabul qilish
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text
    chat_id = update.message.chat_id

    if "instagram" in text:
        await update.message.reply_text("📥 Yuklab olinmoqda... Iltimos kuting.")
        await download_instagram(chat_id, text, context)
    elif "youtu" in text:
        user_data[chat_id] = {"url": text}
        await update.message.reply_text("📥 Yuklab olish turini tanlang:", reply_markup=main_buttons())
    else:
        await update.message.reply_text("❗️ Iltimos, YouTube yoki Instagram link yuboring.")

# 📥 Instagram videoni yuklash
async def download_instagram(chat_id, url, context):
    file_name = f"{chat_id}_insta.mp4"
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_name,
        'merge_output_format': 'mp4',
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(file_name):
            await context.bot.send_message(chat_id, "❗️ Fayl topilmadi.")
            return

        with open(file_name, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption="✅ Instagram videosi tayyor!",
                supports_streaming=True
            )

        await send_reklama(chat_id, context)

    except Exception as e:
        await context.bot.send_message(chat_id, f"❌ Xatolik: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

# 🎧 YouTube yuklash: Audio va Video
async def download_video(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    selected = query.data
    chat_id = query.message.chat.id

    # 🟡 Video menyusini ko‘rsatish
    if selected == "video_menu":
        await query.message.reply_text("📽️ Sifatni tanlang:", reply_markup=quality_buttons())
        return

    # 🔒 Link tekshiruvi (video_menu'dan keyin)
    if chat_id not in user_data:
        await query.message.reply_text("❗️ Avval video link yuboring.")
        return

    url = user_data[chat_id]["url"]

    if selected == "audio":
        file_base = f"{chat_id}_audio"
        file_name = f"{file_base}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{file_base}.%(ext)s",
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if not os.path.exists(file_name):
                await query.message.reply_text("❗️ Audio fayl yaratilmadi.")
                return

            with open(file_name, 'rb') as audio_file:
                await query.message.reply_audio(audio=audio_file, caption="✅ Audio tayyor!")
            await send_reklama(chat_id, context)

        except Exception as e:
            await query.message.reply_text(f"❌ Xatolik: {e}")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    else:
        file_name = f"{chat_id}_{selected}.mp4"
        ydl_opts = {
            'format': f'bestvideo[height<={selected}]+bestaudio/best[height<={selected}]',
            'outtmpl': file_name,
            'merge_output_format': 'mp4',
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if not os.path.exists(file_name):
                await query.message.reply_text("❗️ Video fayl topilmadi.")
                return

            with open(file_name, 'rb') as video_file:
                await query.message.reply_video(video=video_file, caption="✅ Video tayyor!", supports_streaming=True)
            await send_reklama(chat_id, context)

        except Exception as e:
            await query.message.reply_text(f"❌ Xatolik: {e}")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

def main():
    app = (
        Application.builder()
        .token(TOKEN)
        .read_timeout(120)      # ✅ Timeout uzaytirildi
        .write_timeout(120)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(download_video))
    app.run_polling()

if __name__ == '__main__':
    main()