#!/usr/bin/env python3
# Telegram Comment Bot - Render FREE Web + Lifespan (ИСПРАВЛЕННЫЙ 2026-02-02)

import asyncio
import random
import logging
import sys
import os
from collections import deque
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from telethon.tl.types import PeerChannel

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
recent_msgs = deque(maxlen=10000)  # 🆕 Фикс memory leak

@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    global last_comment_time
    
    msg_id = event.id
    chat_id = event.chat_id
    logger.info(f"📨 ПОСТ #{msg_id} chat={chat_id}")
    
    # 🆕 Дедупликация без memory leak
    if msg_id in recent_msgs:
        logger.info(f"⏭️ Дубликат #{msg_id}")
        return
    recent_msgs.append(msg_id)

    # 🔥 Ловим reply_to_message_id (forwarded посты)
    reply_to_id = getattr(event, 'reply_to_msg_id', None) or getattr(event, 'reply_to_reply_to_top_id', None)
    if not reply_to_id:
        logger.info("❌ НЕ reply/forward → игнор")
        return

    # Получаем оригинальный пост
    try:
        original_msg = await client.get_messages(chat_id, ids=reply_to_id)
        logger.info(f"🔗 Reply to #{original_msg.id} from {original_msg.sender_id}")
        
        # 🆕 Фикс: правильная проверка канала
        sender = original_msg.sender_id
        channel_id = None
        if isinstance(sender, PeerChannel):
            channel_id = sender.channel_id
        elif hasattr(sender, 'channel_id'):
            channel_id = sender.channel_id
        
        logger.info(f"📊 Sender: {sender}, Channel ID: {channel_id}")
        
        if channel_id and channel_id in TARGET_CHANNELS:
            logger.info(f"✅ НАШ КАНАЛ {channel_id}!")
        else:
            logger.info(f"❌ НЕ наш канал: {channel_id}")
            return
            
    except Exception as e:
        logger.error(f"❌ Ошибка get_messages: {e}")
        return

    # Рейт-лимит
    now = asyncio.get_event_loop().time()
    if now - last_comment_time < RATE_LIMIT_SECONDS:
        logger.info(f"⏳ Рейт-лимит ({int(now - last_comment_time)}s)")
        return

    # Отправка коммента
    comment = random.choice(messages)
    try:
        sent = await client.send_message(chat_id, comment, reply_to=msg_id)
        last_comment_time = now
        logger.info(f"✅ '{comment}' → #{sent.id} (reply #{msg_id})")
    except FloodWaitError as e:
        logger.warning(f"⏳ FloodWait {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f"❌ Отправка: {e}")

async def telethon_startup():
    """Запуск Telethon"""
    await client.start()
    logger.info(f"🤖 АКТИВЕН: каналы {TARGET_CHANNELS} → группы {GROUPS}")
    
    # Проверка доступа к группам
    for g in GROUPS:
        try:
            entity = await client.get_entity(g)
            logger.info(f"✅ Группа {g} ({entity.title})")
        except Exception as e:
            logger.error(f"❌ Группа {g}: {e}")

    # 🟢 Heartbeat
    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            logger.info("🟢 Bot alive ✅")

    asyncio.create_task(heartbeat())

async def telethon_shutdown():
    """Остановка Telethon"""
    await client.disconnect()
    logger.info('🛑 Telethon остановлен')

@asynccontextmanager
async def lifespan(app: FastAPI):
    await telethon_startup()
    yield
    await telethon_shutdown()

# FastAPI app
app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"status": "Telegram Comment Bot 🔔", "alive": True, "groups": GROUPS}

@app.get("/health")
async def health():
    return {"status": "alive", "listening": True, "rate_limit": RATE_LIMIT_SECONDS}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(
        "comment:app",  # ← имя файла: comment.py
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )




