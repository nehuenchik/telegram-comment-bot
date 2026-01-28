import os
import asyncio
import random
import logging
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import ChatAdminRequiredError, FloodWaitError

# Минимальное логирование для скорости
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

app = FastAPI()

SESSION_STRING = "1BJWap1sBu5TKmL67ra0nnhqoyZzDIGlxtvZI7CFEGlHs3uZ4615SV5gLduhIbWh921RCtpi0wtVCTj7UtaM640EpBY3VEkpKU5GnETdz7Q3UyxPL6SS7INWHMBz5GmoNi4aTHL3SxypkUVoeIZG5TDBtmmveQhNQjfMGkNRZ_6Tr1Euc55MoHAAFf2rp9p2JwNTAqs33OQ29hy4WkiS_TzOedH5WHue2i5Utn-HsiIJdsygUMWz0NYARvkyaHUki475hAVyRBzhF0Q2IY10E172AHsHgwZw4LoZkZqSXk5modWCClKf-epd4ldqdzuEDkbmBucEQMMcARuLNWAHHc5SvlNQLgNQ="

# Расширенный пул сообщений (быстрый random.choice)
messages = [
    'топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
    'лучший', 'интересно', '👍', 'огонь', 'как всегда на уровне'
]

API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

DISCUSSION_GROUPS = [-1001768427632, -1003304394138]
CHANNEL_GROUP_MAP = {
    -1001579090675: -1001768427632,
    -1003485053085: -1003304394138
}

MAIN_AUTHORS = {}
last_commented_msg_id = {}
last_comment_time = {}
MY_ID = None
RATE_LIMIT_SECONDS = 1200  # 20 минут (число для скорости)

@app.get("/healthz")
@app.get("/")
async def health():
    return {"status": "ok", "bot": "⚡ running 24/7", "timestamp": asyncio.get_event_loop().time()}

async def get_channel_authors():
    for channel_id, group_id in CHANNEL_GROUP_MAP.items():
        try:
            async for msg in client.iter_messages(channel_id, limit=1):
                if msg.sender_id:
                    MAIN_AUTHORS[group_id] = msg.sender_id
                    last_commented_msg_id[group_id] = None
                    last_comment_time[group_id] = 0
                    print(f'✅ Group {group_id}: author {msg.sender_id}')
                    break
        except Exception as e:
            print(f'❌ Channel {channel_id}: {e}')

@client.on(events.NewMessage(chats=DISCUSSION_GROUPS))
async def handler(event):
    global MY_ID
    if MY_ID is None:  # быстрый выход если не авторизованы
        return

    group_id = event.chat_id
    msg_id = event.id
    sender_id = event.sender_id

    # 4 быстрых фильтра (return = молния)
    if group_id not in MAIN_AUTHORS or sender_id != MAIN_AUTHORS[group_id]:
        return
    if sender_id == MY_ID:
        return
    if last_commented_msg_id.get(group_id) == msg_id:
        return

    # Лимит 20 мин (быстрое число)
    now = asyncio.get_event_loop().time()
    if now - last_comment_time.get(group_id, 0) < RATE_LIMIT_SECONDS:
        return

    comment = random.choice(messages)

    try:
        await client.send_message(group_id, comment, reply_to=msg_id)
        last_commented_msg_id[group_id] = msg_id
        last_comment_time[group_id] = now
        # Silent mode для скорости (раскомментируй для отладки)
        # print(f'⚡ {comment} -> {msg_id}')
    except ChatAdminRequiredError:
        logger.warning('❌ No write permissions')
    except FloodWaitError as e:
        logger.warning(f'⏳ FloodWait {e.seconds}s')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'❌ Send error: {e}')

async def telethon_task():
    global MY_ID
    await client.start()
    me = await client.get_me()
    MY_ID = me.id
    print(f'🤖 @{me.username} (ID: {MY_ID}) SESSION OK ⚡')
    await get_channel_authors()
    print(f'👥 Groups: {len(DISCUSSION_GROUPS)} | Authors: {len(MAIN_AUTHORS)}')
    print('🚀 ULTRA-FAST BOT READY! Latency <50ms')
    await client.run_until_disconnected()

async def main():
    asyncio.create_task(telethon_task())
    
    config = uvicorn.Config(
        app, host="0.0.0.0", 
        port=int(os.environ.get("PORT", 10000)), 
        log_level="warning"  # минимум логов
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
