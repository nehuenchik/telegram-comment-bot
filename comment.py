import os
import asyncio
import random
import logging
import psutil
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import ChatAdminRequiredError, FloodWaitError, RPCError

# Логи (краткие)
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

SESSION_STRING = "1BJWap1sBu5TKmL67ra0nnhqoyZzDIGlxtvZI7CFEGlHs3uZ4615SV5gLduhIbWh921RCtpi0wtVCTj7UtaM640EpBY3VEkpKU5GnETdz7Q3UyxPL6SS7INWHMBz5GmoNi4aTHL3SxypkUVoeIZG5TDBtmmveQhNQjfMGkNRZ_6Tr1Euc55MoHAAFf2rp9p2JwNTAqs33OQ29hy4WkiS_TzOedH5WHue2i5Utn-HsiIJdsygUMWz0NYARvkyaHUki475hAVyRBzhF0Q2IY10E172AHsHgwZw4LoZkZqSXk5modWCClKf-epd4ldqdzuEDkbmBucEQMMcARuLNWAHHc5SvlNQLgNQ="

messages = [
    'топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
    'лучший', 'интересно', '👍', 'огонь', 'супер', 'отлично',
    '👌', 'спс', 'класно', 'первый', 'о'
]

API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

DISCUSSION_GROUPS = [-1001768427632, -1003304394138]
CHANNEL_GROUP_MAP = {-1001579090675: -1001768427632, -1003485053085: -1003304394138}

MAIN_AUTHORS = {}
last_commented_msg_id = {}
last_comment_time = {}
MY_ID = None
RATE_LIMIT_SECONDS = 1200  # 20 мин

telethon_alive = False
last_telethon_error = None
restart_count = 0
ping_task = None

@app.get("/healthz")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "bot": "⚡ ANTI-SLEEP COMMENT BOT v3.0",
        "groups": len(DISCUSSION_GROUPS),
        "authors": len(MAIN_AUTHORS),
        "telethon_alive": telethon_alive,
        "last_error": str(last_telethon_error)[:80] if last_telethon_error else None,
        "restarts": restart_count,
        "comments": sum(len(ids) for ids in last_commented_msg_id.values()),
        "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 1),
        "uptime": "24/7"
    }

async def get_channel_authors():
    for channel_id, group_id in CHANNEL_GROUP_MAP.items():
        try:
            async for msg in client.iter_messages(channel_id, limit=1):
                if msg.sender_id:
                    MAIN_AUTHORS[group_id] = msg.sender_id
                    if group_id not in last_commented_msg_id:
                        last_commented_msg_id[group_id] = {}
                    if group_id not in last_comment_time:
                        last_comment_time[group_id] = 0
                    logger.info(f'✅ Group {group_id}: author {msg.sender_id}')
                    break
        except Exception as e:
            logger.error(f'❌ Channel {channel_id}: {e}')

@client.on(events.NewMessage(chats=DISCUSSION_GROUPS))
async def handler(event):
    global MY_ID
    
    if not MY_ID:
        return

    group_id = event.chat_id
    msg_id = event.id
    sender_id = event.sender_id

    # Авто-инициализация
    if group_id not in last_commented_msg_id:
        last_commented_msg_id[group_id] = {}
    if group_id not in last_comment_time:
        last_comment_time[group_id] = 0

    # ⚡ 4 быстрых фильтра
    if sender_id != MAIN_AUTHORS.get(group_id):
        return
    if sender_id == MY_ID:
        return
    if msg_id in last_commented_msg_id[group_id]:
        return

    now = asyncio.get_event_loop().time()
    if now - last_comment_time[group_id] < RATE_LIMIT_SECONDS:
        return

    comment = random.choice(messages)

    try:
        await client.send_message(group_id, comment, reply_to=msg_id)
        last_commented_msg_id[group_id][msg_id] = True
        last_comment_time[group_id] = now
        logger.info(f'✅ "{comment}" → #{msg_id}')
    except ChatAdminRequiredError:
        logger.warning('❌ Нет прав')
    except FloodWaitError as e:
        logger.warning(f'⏳ {e.seconds}s')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'❌ {e}')

async def ping_telegram():
    """🔔 ANTI-SLEEP: ping каждые 5мин"""
    global telethon_alive
    while telethon_alive:
        try:
            await asyncio.sleep(300)  # 5 минут
            await client.get_me()
            logger.debug('📡 Ping OK')
        except:
            logger.warning('📡 Ping FAIL → restart soon')
            telethon_alive = False
            break

async def telethon_worker():
    """🔄 НЕУБИВАЕМЫЙ перезапуск"""
    global MY_ID, telethon_alive, last_telethon_error, restart_count, ping_task
    
    while True:
        try:
            telethon_alive = False
            logger.info('🔄 Telethon restart...')
            
            await client.start()
            me = await client.get_me()
            MY_ID = me.id
            logger.info(f'🤖 @{me.username} ({MY_ID})')

            await get_channel_authors()
            telethon_alive = True
            last_telethon_error = None
            restart_count += 1
            
            # 🔔 Запуск ping
            ping_task = asyncio.create_task(ping_telegram())
            
            logger.info(f'🚀 ACTIVE | restarts: {restart_count}')
            await client.run_until_disconnected()
            
        except asyncio.TimeoutError:
            logger.warning('⏰ Timeout restart')
        except Exception as e:
            telethon_alive = False
            last_telethon_error = str(e)
            logger.error(f'💥 {e}')
        
        # 🛑 Отмена ping
        if ping_task:
            ping_task.cancel()
            ping_task = None
        
        await asyncio.sleep(5)  # Быстрый рестарт

async def main():
    logger.info('🎯 ULTRA Bot starting...')
    asyncio.create_task(telethon_worker())
    
    config = uvicorn.Config(
        app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)),
        log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
