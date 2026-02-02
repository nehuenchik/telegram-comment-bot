#!/usr/bin/env python3
# Telegram Comment Bot DEBUG - Render FREE Web + Lifespan
# ✅ ЛОВИТ ВСЕ ПОСТЫ + показывает где застревает!

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
    
    # 🔥 DEBUG: ЛОВИМ ВСЕ ПОСТЫ В ГРУППЕ!
    logger.info(f"📨 ПОСТ #{event.id} chat={event.chat_id}")
    
    msg_id = event.id
    if msg_id in recent_msgs:
        logger.info(f"⏭️ Дубликат #{msg_id}")
        return
    recent_msgs.add(msg_id)

    # 🔥 DEBUG: forwarded?
    logger.info(f"🔄 Forwarded: {bool(event.forward)}")
    if not event.forward:
        logger.info("❌ НЕ forwarded → игнор")
        return

    # 🔥 DEBUG: какой канал?
    forward_channel = getattr(event.forward.from_id, 'channel_id', None)
    logger.info(f"📢 Канал: {forward_channel} (цель: {TARGET_CHANNELS})")
    if forward_channel not in TARGET_CHANNELS:
        logger.info("❌ НЕ наш канал → игнор")
        return

    logger.info("✅ ПРОШЁЛ ФИЛЬТРЫ!")

    if MY_ID is None:
        MY_ID = (await client.get_me()).id
        logger.info(f"👤 Мой ID: {MY_ID}")

    now = asyncio.get_event_loop().time()
    time_passed = now - last_comment_time
    logger.info(f"⏱️ Прошло: {time_passed:.0f}s (нужно {RATE_LIMIT_SECONDS})")
    
    if time_passed < RATE_LIMIT_SECONDS:
        logger.info("⏳ Рейт-лимит → ждём")
        return

    comment = random.choice(messages)
    logger.info(f"💬 Отправляем: '{comment}'")
    
    try:
        sent = await client.send_message(event.chat_id, comment, reply_to=event.id)
        last_comment_time = now
        logger.info(f"✅ '{comment}' #{msg_id} → #{sent.id}")
    except FloodWaitError as e:
        logger.warning(f"⏳ FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")


async def telethon_startup():
    await client.start()
    logger.info(f"🤖 АКТИВЕН: каналы {TARGET_CHANNELS} → группы {GROUPS}")
    
    for g in GROUPS:
        try:
            entity = await client.get_entity(g)
            logger.info(f"✅ Группа {g} '{entity.title}'")
        except Exception as e:
            logger.error(f"❌ {g}: {e}")

    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            logger.info("🟢 Bot alive - ловит посты")

    asyncio.create_task(heartbeat())


async def telethon_shutdown():
    await client.disconnect()
    logger.info('🛑 Telethon остановлен')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await telethon_startup()
    yield
    await telethon_shutdown()


app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Telegram Comment Bot DEBUG 🔔", "alive": True}

@app.get("/health")
async def health():
    return {"status": "alive", "debug": True}


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("comment:app", host="0.0.0.0", port=port, log_level="info")





