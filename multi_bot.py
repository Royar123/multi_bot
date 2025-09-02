import discord
from discord.ext import commands
import asyncio
import os
import random

OWNER_ID = 936086127767617576
allowed_users = set([OWNER_ID])

BOT_TOKENS = []
with open("bot_tokens.txt", "r") as f:
    BOT_TOKENS = [line.strip() for line in f if line.strip()]

bots = []
SPAM_CHANNEL = {}

def is_authorized(ctx):
    return ctx.author.id in allowed_users or ctx.author.id == OWNER_ID

def create_bot(token, index):
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)
    bot.spam_tasks = {}

    @bot.event
    async def on_ready():
        print(f"✅ Bot {index+1} đã đăng nhập: {bot.user}")

    @bot.command(name="menu")
    async def menu(ctx):
        if not is_authorized(ctx): return
        if index == 0:
            await ctx.send("""📜 **Lệnh menu:**
`.menu` - Hiển thị danh sách lệnh  
`.set <channel_id>` - Chọn kênh bot sẽ spam vào  
`.spam <nội_dung> <delay>` - Spam nội dung bạn nhập  
`.spamfile <file.txt> <delay>` - Spam nội dung từ file  
`.spamtag <nội_dung> <user_ids> <delay>` - Spam nội dung kèm tag  
`.spamtagfile <file.txt> <user_ids> <delay>` - Spam từ file + tag nhiều user  
`.spamrolefile <file.txt> <role_id> <delay>` - Spam từ file + tag role  
`.listfiles` - Liệt kê các file .txt   
`.dm <user_id> <nội_dung> <số_lần>` - Gửi DM lặp lại số lần  
`.dms <user_id> <nội_dung> <delay>` - Gửi DM liên tục đến khi dừng  
`.stop` - Dừng spam
""")

    @bot.command()
    async def dm(ctx, user_ids: str, *, args: str):
        if not is_authorized(ctx): return
        try:
            *message_parts, count_str = args.rsplit(" ", 1)
            message = " ".join(message_parts)
            count = int(count_str)
            user_id_list = [uid.strip() for uid in user_ids.split(",")]

            await ctx.send(f"🚀 Đang gửi DM {count} lần đến {len(user_id_list)} người dùng...")

            for uid in user_id_list:
                try:
                    user = await bot.fetch_user(int(uid))
                    for _ in range(count):
                        await user.send(message)
                        await asyncio.sleep(1)
                except Exception as e:
                    await ctx.send(f"⚠️ Không thể gửi tới <@{uid}>: {e}")
            await ctx.send("✅ Hoàn tất gửi DM.")
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @bot.command()
    async def dms(ctx, user_ids: str, *, args: str):
        if not is_authorized(ctx): return
        try:
            *message_parts, delay_str = args.rsplit(" ", 1)
            message = " ".join(message_parts)
            delay = float(delay_str)
            user_id_list = [uid.strip() for uid in user_ids.split(",")]

            await ctx.send(f"🚀 Bắt đầu spam DM đến {len(user_id_list)} người dùng mỗi {delay}s.")

            async def loop():
                while True:
                    for uid in user_id_list:
                        try:
                            user = await bot.fetch_user(int(uid))
                            await user.send(message)
                            await asyncio.sleep(1)
                        except Exception as e:
                            await ctx.send(f"⚠️ Không thể gửi tới <@{uid}>: {e}")
                    await asyncio.sleep(delay)

            bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())
        except Exception as e:
            await ctx.send(f"❌ Không thể bắt đầu spam DM: {e}")

    @bot.command()
    async def add(ctx, user_id: int):
        if ctx.author.id != OWNER_ID: return
        allowed_users.add(user_id)
        await ctx.send(f"✅ Đã thêm <@{user_id}> vào danh sách được phép dùng bot.")

    @bot.command()
    async def remove(ctx, user_id: int):
        if ctx.author.id != OWNER_ID: return
        allowed_users.discard(user_id)
        await ctx.send(f"❌ Đã xoá <@{user_id}> khỏi danh sách được phép dùng bot.")

    @bot.command()
    async def set(ctx, channel_id: int):
        if not is_authorized(ctx): return
        SPAM_CHANNEL[ctx.guild.id] = channel_id
        await ctx.send(f"📢 Đã đặt kênh spam là: <#{channel_id}>")

    @bot.command()
    async def spam(ctx, *, args):
        if not is_authorized(ctx): return
        parts = args.rsplit(" ", 1)
        content = parts[0]
        delay = float(parts[1])
        await ctx.send(f"🚀 Bắt đầu spam `{content}` mỗi {delay}s")
        async def loop():
            while True:
                await ctx.send(content)
                await asyncio.sleep(delay)
        bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())

    @bot.command()
    async def stop(ctx):
        if not is_authorized(ctx): return
        task = bot.spam_tasks.pop(ctx.channel.id, None)
        if task:
            task.cancel()
            await ctx.send("🛑 Đã dừng spam.")
        else:
            await ctx.send("⚠️ Không có spam nào đang chạy.")

    @bot.command()
    async def spamfile(ctx, file: str, delay: float):
        if not is_authorized(ctx): return
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return await ctx.send(f"❌ File `{file}` không tồn tại.")
        await ctx.send(f"🚀 Bắt đầu spam từ file `{file}` mỗi {delay}s")
        async def loop():
            while True:
                await ctx.send(random.choice(lines))
                await asyncio.sleep(delay)
        bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())

    @bot.command()
    async def spamtag(ctx, *, args: str):
        if not is_authorized(ctx): return
        try:
            parts = args.rsplit(" ", 2)
            if len(parts) != 3:
                return await ctx.send("⚠️ Sai cú pháp. Dùng: `.spamtag <nội_dung> <user_ids> <delay>`")

            content, user_ids, delay_str = parts
            delay = float(delay_str)
            mentions = " ".join([f"<@{uid.strip()}>" for uid in user_ids.split(",")])

            await ctx.send(f"🚀 Bắt đầu spam `{content}` với tag: {mentions} mỗi {delay}s")

            async def loop():
                while True:
                    await ctx.send(f"{content} {mentions}")
                    await asyncio.sleep(delay)

            bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {e}")

    @bot.command()
    async def spamtagfile(ctx, file: str, user_ids: str, delay: float):
        if not is_authorized(ctx): return
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return await ctx.send(f"❌ File `{file}` không tồn tại.")
        mentions = " ".join([f"<@{uid.strip()}>" for uid in user_ids.split(",")])
        await ctx.send(f"🚀 Bắt đầu spam tag {mentions} từ `{file}` mỗi {delay}s")
        async def loop():
            while True:
                await ctx.send(f"{random.choice(lines)} {mentions}")
                await asyncio.sleep(delay)
        bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())

    @bot.command()
    async def spamrolefile(ctx, file: str, role_id: int, delay: float):
        if not is_authorized(ctx): return
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            return await ctx.send(f"❌ File `{file}` không tồn tại.")
        mention = f"<@&{role_id}>"
        await ctx.send(f"🚀 Bắt đầu spam tag role {mention} từ `{file}` mỗi {delay}s")
        async def loop():
            while True:
                await ctx.send(f"{random.choice(lines)} {mention}")
                await asyncio.sleep(delay)
        bot.spam_tasks[ctx.channel.id] = asyncio.create_task(loop())

    @bot.command()
    async def listfiles(ctx):
        if not is_authorized(ctx): return
        files = [f for f in os.listdir() if f.endswith(".txt")]
        if files:
            await ctx.send("📂 Các file .txt:\n" +
 "\n".join([f"`{f}`" for f in files]))
        else:
            await ctx.send("❌ Không tìm thấy file .txt nào.")

    return bot

# Chạy toàn bộ bot song song
async def main():
    for idx, token in enumerate(BOT_TOKENS):
        try:
            bot = create_bot(token, idx)
            bots.append(bot)
            asyncio.create_task(bot.start(token))
        except Exception as e:
            print(f"❌ Lỗi khởi động bot {idx+1}: {e}")

    while True:
        await asyncio.sleep(3600)

# === Keep Alive cho Replit ===
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Gọi keep_alive và chạy bot
keep_alive()
asyncio.run(main())
