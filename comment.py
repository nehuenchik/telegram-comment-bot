#!/usr/bin/env python3
# Telegram Comment Bot - Render FREE Web + Lifespan (обновлённый)

import asyncio
import random
import logging
import sys
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

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

SESSION_STRING = "1BJWap1wBu7jsW2CiWoCtwLJh5GTNL4gXLM_zTnHQhd10Uo00Ebeer1oOoha3yDKjrEwfw9hfvv44KzCpHCK9BLcNU8gkfDsN-PWuuN6MB7WAsklvLOlzOSzD5f1Adc1QT6ojaXyVajWvE3Olhu8dtnvGsWUMsyrcErHAsPMnn0aKAdv-r3ahm_hF5-ramtHjnN38IAI3AzmSo4r0ZR5URMYpvJpF8bGsbLx0s1WXIhE_iw0uP3ExdJyM1swiE4uapnyqf1acH91dmkpGdU7h6qwzvWbvvAaaSWYO-b3ffF4DYEt_OxZa7gb9tIavzL74RijRbOhFTqsYmRhuf704K_mJgqjAyok="
API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

TARGET_CHANNELS = [1579090675, 3485053085]
GROUPS = [-1001768427632, -1003304394138]

RATE_LIMIT_SECONDS = 600
messages = ['топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
            'лучший', 'интересно', '👍', 'огонь', 'супер', 'отлично',
            '👌', 'спс', 'класно', 'первый', 'о']

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


async def telethon_startup():
    """Запуск Telethon"""
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


async def telethon_shutdown():
    """Остановка Telethon"""
    await client.disconnect()
    logger.info('🛑 Telethon stopped')


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: запускаем Telethon
    await telethon_startup()
    yield
    # Shutdown
    await telethon_shutdown()


# Современный FastAPI Lifespan (без warning)
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Telegram Comment Bot 🔔", "alive": True}

@app.get("/health")
async def health():
    return {"status": "alive", "listening": True}


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(
        "comment:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )





