#!/usr/bin/env python3
# Telegram Comment Bot v2.0 - Render FREE 24/7 (2026-02-02 ULTRA)

import asyncio
import random
import logging
import sys
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
import uvicorn

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import PeerChannel, Channel

os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# 🔒 Конфиг (env vars для безопасности)
SESSION_STRING = os.getenv('SESSION_STRING', "1BJWap1wBu7jsW2CiWoCtwLJh5GTNL4gXLM_zTnHQhd10Uo00Ebeer1oOoha3yDKjrEwfw9hfvv44KzCpHCK9BLcNU8gkfDsN-PWuuN6MB7WAsklvLOlzOSzD5f1Adc1QT6ojaXyVajWvE3Olhu8dtnvGsWUMsyrcErHAsPMnn0aKAdv-r3ahm_hF5-ramtHjnN38IAI3AzmSo4r0ZR5URMYpvJpF8bGsbLx0s1WXIhE_iw0uP3ExdJyM1swiE4uapnyqf1acH91dmkpGdU7h6qwzvWbvvAaaSWYO-b3ffF4DYEt_OxZa7gb9tIavzL74RijRbOhFTqsYmRhuf704K_mJgqjAyok=")
API_ID = int(os.getenv('API_ID', '23315051'))
API_HASH = os.getenv('API_HASH', '927ac8e4ddfc1092134b414b1a17f5bd')

TARGET_CHANNELS = [1579090675, 3485053085]  # ID каналов
GROUPS = [-1001768427632, -1003304394138]   # ID групп

RATE_LIMIT_SECONDS = int(os.getenv('RATE_LIMIT', '600'))
COMMENT_DELAY_MIN = int(os.getenv('COMMENT_DELAY_MIN', '5'))  # Случайная задержка

messages = [
    'топ', '1️⃣', 'спасибо!', '🔥🔥', 'круто!', 'благодарю 💯',
    'лучший контент', 'интересно 👍', 'огонь 🔥', 'супер!', 'отлично 👌',
    'спс!', 'класс!', 'первый!', '💪', 'wow'
]

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
stats = {'comments': 0, 'processed': 0, 'errors': 0, 'start_time': time.time()}
recent_msgs = deque(maxlen=50000)
last_comment_time = 0

def get_channel_id(sender_id: Optional[object]) -> Optional[int]:
    """🆕 Безопасная проверка channel_id"""
    if not sender_id:
        return None
    if isinstance(sender_id, PeerChannel):
        return sender_id.channel_id
    if isinstance(sender_id, Channel):
        return sender_id.id
    if hasattr(sender_id, 'channel_id'):
        return getattr(sender_id, 'channel_id')
    return None

@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    global last_comment_time
    stats['processed'] += 1
    
    msg_id = event.id
    chat_id = event.chat_id
    
    logger.debug(f"📨 #{msg_id} chat={chat_id}")
    
    # Дедупликация
    if msg_id in recent_msgs:
        return
    recent_msgs.append(msg_id)

    # 🔥 Forwarded/reply ловля (улучшено)
    reply_to_id = (event.reply_to_msg_id or 
                   event.reply_to_reply_to_top_id or 
                   getattr(event, 'fwd_from_id', None))
    
    if not reply_to_id:
        return

    try:
        # Получаем оригинал
        original_msg = await client.get_messages(chat_id, ids=reply_to_id)
        channel_id = get_channel_id(original_msg.sender_id)
        
        logger.info(f"🔍 #{original_msg.id} → channel={channel_id}")
        
        if channel_id not in TARGET_CHANNELS:
            return
            
        logger.info(f"✅ TARGET {channel_id}!")
        
    except Exception as e:
        stats['errors'] += 1
        logger.debug(f"❌ Parse: {e}")
        return

    # 🆕 Умный рейт-лимит + рандом задержка
    now = asyncio.get_event_loop().time()
    wait_time = now - last_comment_time
    if wait_time < RATE_LIMIT_SECONDS:
        logger.debug(f"⏳ Wait {int(wait_time)}s")
        return
    
    # Случайная задержка 5-30 сек
    await asyncio.sleep(random.randint(COMMENT_DELAY_MIN, 30))
    
    comment = random.choice(messages)
    try:
        sent = await client.send_message(chat_id, comment, reply_to=msg_id)
        last_comment_time = asyncio.get_event_loop().time()
        stats['comments'] += 1
        logger.info(f"✅ {comment} → #{sent.id} | Total: {stats['comments']}")
        
    except FloodWaitError as e:
        logger.warning(f"⏳ FLOOD {e.seconds}s")
        await asyncio.sleep(e.seconds)
        stats['errors'] += 1
    except Exception as e:
        logger.error(f"❌ Send: {e}")
        stats['errors'] += 1

async def telethon_lifecycle():
    """🚀 Автозапуск + reconnect"""
    reconnects = 0
    while True:
        try:
            await client.start()
            logger.info(f"🤖 v2.0 LIVE | каналы: {TARGET_CHANNELS}")
            
            # Проверка групп
            for g in GROUPS:
                try:
                    entity = await client.get_entity(g)
                    logger.info(f"✅ {g} '{entity.title}'")
                except:
                    logger.warning(f"⚠️ Нет доступа {g}")
            
            # Heartbeat + stats
            while True:
                await asyncio.sleep(300)
                uptime = int(time.time() - stats['start_time'])
                logger.info(f"🟢 Alive | Комменты: {stats['comments']} | "
                          f"Обработано: {stats['processed']} | Uptime: {uptime//3600}h")
                
        except SessionPasswordNeededError:
            logger.error("🔒 2FA пароль нужен!")
            break
        except Exception as e:
            reconnects += 1
            logger.error(f"💥 Crash #{reconnects}: {e}")
            await asyncio.sleep(60 * reconnects)  # Exponential backoff

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(telethon_lifecycle())
    yield
    await client.disconnect()

# 🌐 FastAPI API
app = FastAPI(title="Telegram Bot API", lifespan=lifespan)

@app.get("/")
async def root():
    uptime = int(time.time() - stats['start_time'])
    return {
        "status": "🔔 Telegram Comment Bot v2.0",
        "alive": True,
        "comments": stats['comments'],
        "uptime_hours": uptime // 3600,
        "groups": GROUPS
    }

@app.get("/health")
async def health():
    return {
        "status": "alive",
        "comments": stats['comments'],
        "processed": stats['processed'],
        "errors": stats['errors'],
        "rate_limit": RATE_LIMIT_SECONDS
    }

@app.get("/stats")
async def stats_endpoint():
    uptime = int(time.time() - stats['start_time'])
    return {
        **stats,
        "uptime_sec": uptime,
        "success_rate": stats['comments'] / max(stats['processed'], 1) * 100
    }

@app.post("/reset-stats")
async def reset_stats():
    stats.update({'comments': 0, 'processed': 0, 'errors': 0})
    return {"reset": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("comment:app", host="0.0.0.0", port=port, log_level="info")




