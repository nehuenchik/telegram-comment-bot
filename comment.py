import asyncio
import random
import logging
import sys
import os

from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}

SESSION_STRING = "..."
API_ID = 23315051
API_HASH = "927ac8e4ddfc1092134b414b1a17f5bd"

TARGET_CHANNELS = [1579090675, 3485053085]
GROUPS = [-1001768427632, -1003304394138]

RATE_LIMIT_SECONDS = 600
messages = [...]
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
last_comment_time = 0
MY_ID = None
recent_msgs = set()


@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    global last_comment_time, MY_ID, recent_msgs
    msg_id = event.id
    if msg_id in recent_msgs:
        return
    recent_msgs.add(msg_id)

    if not event.forward:
        return

    forward_channel = getattr(event.forward.from_id, 'channel_id', None)
    if forward_channel not in TARGET_CHANNELS:
        return

    if MY_ID is None:
        MY_ID = (await client.get_me()).id

    now = asyncio.get_event_loop().time()
    if now - last_comment_time < RATE_LIMIT_SECONDS:
        return

    comment = random.choice(messages)
    try:
        await client.send_message(event.chat_id, comment, reply_to=event.id)
        last_comment_time = now
        logger.info(f"✅ {comment} #{msg_id}")
    except FloodWaitError as e:
        logger.warning(f"⏳ FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f"❌ {e}")


async def telethon_worker():
    await client.start()
    logger.info(f"🤖 АКТИВЕН: {TARGET_CHANNELS} → {GROUPS}")
    for g in GROUPS:
        try:
            await client.get_entity(g)
            logger.info(f"✅ Группа {g}")
        except Exception as e:
            logger.error(f"❌ {g}: {e}")

    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            logger.info("🟢 Bot alive")

    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()


@app.on_event("startup")
async def startup_event():
    # запускаем Telethon как фон-таск в том же loop, где крутится FastAPI
    asyncio.create_task(telethon_worker())




