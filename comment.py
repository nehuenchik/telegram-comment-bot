#!/usr/bin/env python3
# Telegram Comment Bot - Render FREE Web Service + FastAPI Healthcheck
# Комментирует ТОЛЬКО forwarded посты от каналов → 24/7 БЕСПЛАТНО!

import asyncio
import random
import logging
import sys
import os

from fastapi import FastAPI
import uvicorn

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ✅ Render FREE: логи + порт
os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

# FastAPI для Render Web Service (healthcheck)
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "Telegram Comment Bot 🔔", "alive": True}

@app.get("/health")
async def health():
    return {"status": "alive", "telethon": "listening", "uptime": "24/7"}

SESSION_STRING = "1BJWap1wBux2jgHDja76evZiaiSp4ZjoGGb_biQVh9kOdYBKm9LKqKoSt-XhtAxMcE7DjErX53ntwQDfRzzCuKsp7BLcRClCQOSNdA0pYY7sHg4gbirA62RdD0gXVEe7yIWLVCdcBgdJTYq__IEgL3WKyN7IDchaxD2skwH6CaVAAMJVqEevsS53fxT6SrkxtM1LxmLPP8Wip2Jt_P0MzbhDozIAerFoituBlXuBFCLHQA8wG8aL-rUwv3H-5G9wxmE4onxhHr4RdowNfewnaPTQPgzYNZajLuxt-O53kdm0FFHB-_Se6Uc_G5LfiumSMLWay2XeB7mXaNTwVwzvwq4I4Kgm-12M="
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
    time_passed = now - last_comment_time

    if time_passed >= RATE_LIMIT_SECONDS:
        comment = random.choice(messages)
        try:
            await client.send_message(event.chat_id, comment, reply_to=event.id)
            last_comment_time = now
            logger.info(f'✅ {comment} под постом #{msg_id}')
        except FloodWaitError as e:
            logger.warning(f'⏳ FloodWait {e.seconds}s')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f'❌ {e}')


async def telethon_task():
    """Telethon в фоне"""
    await client.start()
    logger.info(f'🤖 АКТИВЕН: каналы {TARGET_CHANNELS} → группы {GROUPS}')

    for group in GROUPS:
        try:
            await client.get_entity(group)
            logger.info(f'✅ Группа {group}')
        except Exception as e:
            logger.error(f'❌ {group}: {e}')

    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            logger.info('🟢 Bot alive')

    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()


async def main():
    """Запуск FastAPI + Telethon параллельно"""
    await asyncio.gather(
        telethon_task(),
        asyncio.to_thread(uvicorn.run, app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    )


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🛑 Stop')




