import os
import json
import logging
import secrets
import threading
import time
import requests
import asyncio
from pyrogram.enums import ParseMode
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask
from flask_restful import Resource, Api
from Japanese.mongodb import save_user, save_group
from Japanese.mongodb import (
    get_users_count,
    get_groups_count,
    get_all_user_ids,
    get_all_group_ids
)
from pyrogram.enums import ChatMemberStatus
from pymongo import MongoClient
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ApiIdInvalid, ApiIdPublishedFlood, AccessTokenInvalid
from datetime import datetime, timedelta, timezone
# -------------------- CONFIG -------------------- #
# -------------------- CONFIG -------------------- #

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PING_URL = os.environ.get("PING_URL", "https://beta-test-vuty.onrender.com")

# MongoDB URL (add this)
MONGO_URL = os.environ.get("MONGO_URL", "")
FORCE_CHANNEL = -1003806743202
OWNER_ID = [
    7208410467,
    8623025855
]

LINK_EXPIRE_SECONDS = 60
LINK_MEMBER_LIMIT = 1

# -------------------- KEEP ALIVE -------------------- #
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    logging.info(f"[Flask] Running server on port {port}")
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    url = os.environ.get("PING_URL", "").strip()

    if not url:
        logging.warning("[KeepAlive] PING_URL not set, skipping keep-alive")
        return

    while True:
        try:
            logging.info(f"[KeepAlive] Pinging {url}")
            requests.get(url, timeout=10)
        except Exception as e:
            logging.warning(f"[KeepAlive ERROR] {e}")

        time.sleep(600)  # Ping every 10 minutes

mongo = MongoClient(MONGO_URL)
db = mongo["TechX"]
groups_col = db["groups"]




        
# -------------------- LOGGING -------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- BOT -------------------- #
bot = Client(
    "TechXbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------- STORAGE -------------------- #



def register_group(chat_id, title):
    existing = groups_col.find_one({"chat_id": chat_id})

    if existing:
        return existing["token"]  # same token return

    token = secrets.token_urlsafe(8)

    groups_col.insert_one({
        "chat_id": chat_id,
        "title": title,
        "token": token
    })

    return token


def get_group(token):
    return groups_col.find_one({"token": token})
    


def unregister_group(chat_id):
    groups_col.delete_one({"chat_id": chat_id})



def get_groups():
    return list(groups_col.find())


       






# -------------------- GBAN SYSTEM -------------------- #
GBAN_FILE = Path("gban.json")

# -------------------- HELPERS -------------------- #
def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
def load_gbans():
    if GBAN_FILE.exists():
        return json.loads(GBAN_FILE.read_text())
    return {"users": {}}


def save_gbans(data):
    GBAN_FILE.write_text(json.dumps(data, indent=2))


def add_gban(user_id: int, reason: str = "No reason"):
    data = load_gbans()
    data["users"][str(user_id)] = {
        "reason": reason,
        "time": datetime.now().isoformat()
    }
    save_gbans(data)


def remove_gban(user_id: int):
    data = load_gbans()
    data["users"].pop(str(user_id), None)
    save_gbans(data)


def is_gbanned(user_id: int):
    data = load_gbans()
    return str(user_id) in data["users"]


def get_gban_list():
    return load_gbans().get("users", {})




@bot.on_message(filters.command("stats") & filters.user(OWNER_ID))
async def stats_handler(bot, msg):
    users = get_users_count()
    groups = get_groups_count()

    text = f"""
━━━━━━━━━━━━━━━━━━━
📊 <b>ᴅᴧᴛᴧʙᴧꜱᴇ sᴛᴧᴛs</b>

👤 <b>ᴜsᴇʀs:</b> <code>{users}</code>
👥 <b>ɢʀᴏᴜᴘs:</b> <code>{groups}</code>

🧠 <b>ᴛᴏᴛᴧʟ:</b> <code>{users + groups}</code>
━━━━━━━━━━━━━━━━━━━
"""

    await msg.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


@bot.on_chat_member_updated()
async def handle_bot_added(client, event):
    try:
        me = await client.get_me()

        if not event.new_chat_member:
            return

        if event.new_chat_member.user.id != me.id:
            return

        chat = event.chat

        # BOT ADDED
        if event.new_chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR
        ]:

            token = register_group(chat.id, chat.title)

            link = f"https://t.me/{me.username}?start={token}"


            # ================= CHANNEL =================
            if chat.type == "channel":

                # Owner DM notification
                try:
                    await client.send_message(
                        OWNER_ID,
                        f"""
📢 New Channel Connected

🏷 Name:
{chat.title}

🆔 Channel ID:
{chat.id}

🔗 Control Link:
{link}

✅ Channel Secured
"""
                    )
                except Exception as e:
                    print("Owner DM Error:", e)


                # Try send in channel
                try:
                    await client.send_message(
                        chat.id,
                        f"""
✅ Bot Activated

🔗 Setup Link:
{link}
"""
                    )

                except Exception as e:
                    print("Channel Message Error:", e)


                return



            # ================= GROUP =================
            try:
                await client.send_message(
                    chat.id,
                    f"✅ Setup done!\n\nShare:\n{link}"
                )

            except Exception as e:
                print(f"[Group Send Error] {e}")


            # Owner DM
            try:
                await client.send_message(
                    OWNER_ID,
                    f"""
📢 New Group Added

👥 Name:
{chat.title}

🆔 Chat ID:
{chat.id}

🔗 Link:
{link}
"""
                )

            except Exception as e:
                print("Owner Error:", e)



        # BOT REMOVED
        elif event.new_chat_member.status in [
            ChatMemberStatus.LEFT,
            ChatMemberStatus.BANNED
        ]:
            unregister_group(chat.id)


    except Exception as e:
        print(f"[Handler Error] {e}")


















# -------------------- Auto Save Users & Groups -------------------- #
@bot.on_message(filters.all, group=10)
async def auto_save_handler(bot, msg):
    try:
        if msg.from_user:
            await save_user(msg.from_user)

        if msg.chat and msg.chat.type in ["group", "supergroup"]:
            await save_group(msg.chat)

    except Exception as e:
        print(f"[MONGO SAVE ERROR] {e}")

@bot.on_message(filters.all, group=-1)
async def gban_guard(bot, msg):
    try:
        if msg.from_user and is_gbanned(msg.from_user.id):
            try:
                await msg.delete()
            except:
                pass
            return
    except:
        pass














@bot.on_message(filters.command("broadcast_user") & filters.user(OWNER_ID))
async def broadcast_users(bot, msg):
    if not msg.reply_to_message:
        return await msg.reply_text("❌ Reply to a message to broadcast.")

    sent = 0
    failed = 0

    for user_id in get_all_user_ids():
        try:
            await msg.reply_to_message.forward(user_id)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    await msg.reply_text(
        f"✅ **Broadcast Completed**\n\n"
        f"👤 Sent: `{sent}`\n"
        f"❌ Failed: `{failed}`"
    )


@bot.on_message(filters.command("broadcast_group") & filters.user(OWNER_ID))
async def broadcast_groups(bot, msg):
    if not msg.reply_to_message:
        return await msg.reply_text("❌ Reply to a message to broadcast.")

    sent = 0
    failed = 0

    for group_id in get_all_group_ids():
        try:
            await msg.reply_to_message.forward(group_id)
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1

    await msg.reply_text(
        f"✅ **Group Broadcast Done**\n\n"
        f"👥 Sent: `{sent}`\n"
        f"❌ Failed: `{failed}`"
                  )


@bot.on_message(filters.command("broadcast_all") & filters.user(OWNER_ID))
async def broadcast_all(bot, msg):
    if not msg.reply_to_message:
        return await msg.reply_text("❌ Reply to a message to broadcast.")

    sent = 0
    failed = 0

    # ---- USERS ----
    for user_id in get_all_user_ids():
        try:
            await msg.reply_to_message.forward(user_id)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1

    # ---- GROUPS ----
    for group_id in get_all_group_ids():
        try:
            await msg.reply_to_message.forward(group_id)
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1

    await msg.reply_text(
        f"""
━━━━━━━━━━━━━━━━━━━
📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴀʟʟ ᴄᴏᴍᴘʟᴇᴛᴇ**

✅ **sᴇɴᴛ:** `{sent}`
❌ **failed:** `{failed}`

━━━━━━━━━━━━━━━━━━━
"""
    )


@bot.on_message(filters.command("gban") & filters.user(OWNER_ID))
async def gban_user(bot, msg):
    if not msg.reply_to_message:
        return await msg.reply("❌ Reply to a user")

    user = msg.reply_to_message.from_user
    reason = " ".join(msg.command[1:]) if len(msg.command) > 1 else "No reason"
    username = user.username or "no_username"

    add_gban(user.id, reason)

    # 🔥 BAN FROM ALL GROUPS
    for group_id in get_all_group_ids():
        try:
            await bot.ban_chat_member(group_id, user.id)
        except:
            pass

    text = f"""
━━━━━━━━━━━━━━━━━━━━━━
        𝗚𝗟𝗢𝗕𝗔𝗟 𝗕𝗔𝗡 𝗦𝗬𝗦𝗧𝗘𝗠
━━━━━━━━━━━━━━━━━━━━━━

🚫 𝗦𝗧𝗔𝗧𝗨𝗦      ➜ 𝗣𝗘𝗥𝗠𝗔𝗡𝗘𝗡𝗧𝗟𝗬 𝗕𝗔𝗡𝗡𝗘𝗗
🧾 𝗦𝗧𝗔𝗠𝗣        ➜ 𝗚𝗟𝗢𝗕𝗔𝗟 𝗘𝗡𝗙𝗢𝗥𝗖𝗘𝗠𝗘𝗡𝗧

⏰ 𝗧𝗜𝗠𝗘         ➜ {get_time()}
⏳ 𝗗𝗨𝗥𝗔𝗧𝗜𝗢𝗡    ➜ 𝗜𝗡𝗗𝗘𝗙𝗜𝗡𝗜𝗧𝗘

👤 𝗨𝗦𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦
━━━━━━━━━━━━━━━━━━━━━━
• 𝗡𝗔𝗠𝗘       ➜ @{username}
• 𝗨𝗦𝗘𝗥 𝗜𝗗     ➜ {user.id}
• 𝗣𝗥𝗢𝗙𝗜𝗟𝗘    ➜ https://t.me/{username}

📛 𝗥𝗘𝗔𝗦𝗢𝗡
━━━━━━━━━━━━━━━━━━━━━━
➜ {reason}

⚡ 𝗔𝗖𝗧𝗜𝗢𝗡
━━━━━━━━━━━━━━━━━━━━━━
✔ Removed from all groups
✔ Blocked from bot system
✔ Entry permanently denied

━━━━━━━━━━━━━━━━━━━━━━
        
━━━━━━━━━━━━━━━━━━━━━━
"""

    await msg.reply_text(text)




















@bot.on_message(filters.command("ungban") & filters.user(OWNER_ID))
async def ungban_user(bot, msg):
    if not msg.reply_to_message:
        return await msg.reply("❌ Reply to a user")

    user = msg.reply_to_message.from_user
    username = user.username or "no_username"

    remove_gban(user.id)

    # 🔓 UNBAN FROM ALL GROUPS
    for group_id in get_all_group_ids():
        try:
            await bot.unban_chat_member(group_id, user.id)
        except:
            pass

    text = f"""
━━━━━━━━━━━━━━━━━━━━━━
      𝗚𝗟𝗢𝗕𝗔𝗟 𝗨𝗡𝗕𝗔𝗡 𝗦𝗬𝗦𝗧𝗘𝗠
━━━━━━━━━━━━━━━━━━━━━━

✅ 𝗦𝗧𝗔𝗧𝗨𝗦      ➜ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗥𝗘𝗦𝗧𝗢𝗥𝗘𝗗
🧾 𝗦𝗧𝗔𝗠𝗣        ➜ 𝗖𝗟𝗘𝗔𝗡 𝗥𝗘𝗦𝗘𝗧

⏰ 𝗧𝗜𝗠𝗘         ➜ {get_time()}

👤 𝗨𝗦𝗘𝗥 𝗗𝗘𝗧𝗔𝗜𝗟𝗦
━━━━━━━━━━━━━━━━━━━━━━
• 𝗡𝗔𝗠𝗘       ➜ @{username}
• 𝗨𝗦𝗘𝗥 𝗜𝗗     ➜ {user.id}
• 𝗣𝗥𝗢𝗙𝗜𝗟𝗘    ➜ https://t.me/{username}

📛 𝗔𝗖𝗧𝗜𝗢𝗡
━━━━━━━━━━━━━━━━━━━━━━
➜ Removed from global blacklist
➜ Restored in all groups
➜ Bot access re-enabled

━━━━━━━━━━━━━━━━━━━━━━
        
━━━━━━━━━━━━━━━━━━━━━━
"""

    await msg.reply_text(text)
















@bot.on_message(filters.command("gbanlist") & filters.user(OWNER_ID))
async def list_gbans(bot, msg):
    data = get_gban_list()

    if not data:
        return await msg.reply("✅ No GBANNED users")

    text = """
━━━━━━━━━━━━━━━━━━━━━━
🚫 𝗚𝗟𝗢𝗕𝗔𝗟 𝗕𝗔𝗡 𝗟𝗜𝗦𝗧
━━━━━━━━━━━━━━━━━━━━━━
"""

    for uid, info in data.items():
        text += f"\n👤 `{uid}`\n📛 {info['reason']}\n━━━━━━━━━━━━━━"

    await msg.reply(text)













async def force_joined(client, user_id):
    try:
        member = await client.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER
        ]
    except:
        return False


@bot.on_callback_query(filters.regex("^check_join$"))
async def check_join(client, query):
    user_id = query.from_user.id

    if await force_joined(client, user_id):
        await query.message.edit("✅ Verified! Now use /start again.")
    else:
        await query.answer("❌ You have not joined the channel yet.", show_alert=True)



# -------------------- START -------------------- #


@bot.on_message(filters.command("start"))
async def start(client, message):
    user = message.from_user
    user_id = user.id
    args = message.text.split()

    # 🔥 FORCE JOIN CHECK
    if not await force_joined(client, user_id):
        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url="https://t.me/+7YK56AjMBUVmNjZl"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 I've Joined",
                    callback_data="check_join"
                )
            ]
        ])

        return await message.reply(
            "⚠️ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗥𝗘𝗦𝗧𝗥𝗜𝗖𝗧𝗘𝗗\n\n"
            "You must join our official channel to use this bot.\n"
            "After joining, click **I've Joined** to continue.",
            reply_markup=btn
        )

    # 🔗 GROUP LINK MODE (IMPORTANT PART)
    if len(args) > 1:
        token = args[1]
        group = get_group(token)

        if not group:
            return await message.reply("❌ Invalid or expired link")

        title = group["title"]
        chat_id = group["chat_id"]

        bot_username = (await client.get_me()).username
        start_link = f"https://t.me/{bot_username}?start={token}"

        # 🔔 OWNER NOTIFY (WITH GROUP INFO)
        try:
            for owner in OWNER_ID:
                await client.send_message(
                    owner,
                    f"""
🚀 User Used Invite Link

👤 Name: {user.first_name}
🔗 Username: @{user.username if user.username else "None"}
🆔 User ID: {user.id}

👥 Group: {title}
🆔 Chat ID: {chat_id}
🔗 Link: {start_link}
"""
                )
        except Exception as e:
            print(f"[Owner Notify Error] {e}")

        btn = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"🚀 Join {title}",
                    callback_data=f"gen:{token}"
                )
            ]
        ])

        return await message.reply(
            f"✨ **Invitation Received**\n\n"
            f"🏷 Group: {title}\n\n"
            f"Click below to generate your secure invite link.",
            reply_markup=btn
        )

    # 🔔 NORMAL START (NO TOKEN)
    try:
        for owner in OWNER_ID:
            await client.send_message(
                owner,
                f"""
👤 New User Started Bot

Name: {user.first_name}
Username: @{user.username if user.username else "None"}
User ID: {user.id}
"""
            )
    except Exception as e:
        print(f"[Owner Notify Error] {e}")

    # 🏁 DEFAULT START MENU
    bot_username = (await client.get_me()).username

    btn = InlineKeyboardMarkup([
    [
        InlineKeyboardButton(
            "👥 Add To Group",
            url=f"https://t.me/{bot_username}?startgroup=true"
        )
    ],
    [
        InlineKeyboardButton(
            "📢 Add To Channel",
            url=f"https://t.me/{bot_username}?startchannel&admin=post_messages"
        )
    ]
])

    await message.reply(
        "👋 Welcome!\n\n"
        "Add me to your group to manage invites, bans, and security features.",
        reply_markup=btn
    )















































# -------------------- CALLBACK -------------------- #
@bot.on_callback_query(filters.regex("^gen:"))
async def generate_link(client, query):
    token = query.data.split(":")[1]
    group = get_group(token)

    if not group:
        return await query.message.edit("❌ Group not found")

    chat_id = group["chat_id"]
    title = group["title"]

    expire = datetime.now(timezone.utc) + timedelta(seconds=LINK_EXPIRE_SECONDS)

    try:
        invite = await client.create_chat_invite_link(
            chat_id,
            expire_date=expire,
            member_limit=LINK_MEMBER_LIMIT
        )
    except Exception as e:
        logger.error(e)
        return await query.message.edit("❌ Failed to create link")

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Join {title}", url=invite.invite_link)]
    ])

    await query.message.edit(
        f"✅ Link ready (valid {LINK_EXPIRE_SECONDS}s)",
        reply_markup=btn
    )

# -------------------- GROUP JOIN -------------------- #


# -------------------- OWNER COMMAND -------------------- #
@bot.on_message(filters.command("status") & filters.user(OWNER_ID))
async def status(client, message):
    groups = get_groups()

    if not groups:
        return await message.reply("No groups")

    text = f"Total Groups: {len(groups)}\n\n"

    for g in get_groups():
        text += f"{g['title']} → {g['chat_id']}\nToken: {g['token']}\n\n"
        await message.reply(text)

# -------------------- FLASK -------------------- #
flask_app = Flask(__name__)
api = Api(flask_app)

class Home(Resource):
    def get(self):
        return {"status": "running"}

api.add_resource(Home, "/")

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# -------------------- KEEP ALIVE -------------------- #
def ping():
    if not PING_URL:
        return
    while True:
        try:
            requests.get(PING_URL)
        except:
            pass
        time.sleep(600)

# -------------------- MAIN -------------------- #
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()

    if PING_URL:
        threading.Thread(target=ping, daemon=True).start()

    try:
        logger.info("🚀 Starting bot...")
        bot.start()
        logger.info(f"🤖 Running as @{bot.me.username}")
        idle()

    except (ApiIdInvalid, ApiIdPublishedFlood):
        logger.error("❌ Invalid API ID / HASH")
    except AccessTokenInvalid:
        logger.error("❌ Invalid BOT TOKEN")
    finally:
        bot.stop()
        logger.info("🛑 Bot stopped")
