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
last_comment_time = {}
MY_ID = None
RATE_LIMIT_SECONDS = 600  # 10 минут

telethon_alive = False
last_telethon_error = None
restart_count = 0
ping_task = None


@app.get("/healthz")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "bot": "⚡ COMMENT BOT DEBUG v3.1",
        "groups": len(DISCUSSION_GROUPS),
        "authors": len(MAIN_AUTHORS),
        "authors_list": dict(MAIN_AUTHORS),  # 🔥 ПОКАЗЫВАЕТ ID авторов
        "telethon_alive": telethon_alive,
        "my_id": MY_ID,
        "last_error": str(last_telethon_error)[:80] if last_telethon_error else None,
        "restarts": restart_count,
        "last_comments": {g: f"{int(time.time() - t)}s ago" for g, t in last_comment_time.items()},
        "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 1),
        "uptime": "24/7"
    }


async def get_channel_authors():
    """🔍 Автоопределение авторов + fallback"""
    global MAIN_AUTHORS
    logger.info("🔍 Scanning channels for authors...")
    
    for channel_id, group_id in CHANNEL_GROUP_MAP.items():
        try:
            # Пробуем последнее сообщение
            async for msg in client.iter_messages(channel_id, limit=5):  # +5 для надёжности
                if msg.sender_id and msg.sender_id != MY_ID:
                    MAIN_AUTHORS[group_id] = msg.sender_id
                    if group_id not in last_comment_time:
                        last_comment_time[group_id] = 0
                    logger.info(f'✅ Group {group_id}: author {msg.sender_id}')
                    break
            else:
                logger.warning(f'⚠️ No author found in {channel_id}')
        except Exception as e:
            logger.error(f'❌ Channel {channel_id}: {e}')
    
    if not MAIN_AUTHORS:
        logger.error("💥 NO AUTHORS FOUND! Check CHANNEL_GROUP_MAP IDs")


@client.on(events.NewMessage(chats=DISCUSSION_GROUPS))
async def handler(event):
    global MY_ID

    if not MY_ID:
        logger.debug("⏳ MY_ID not ready")
        return

    group_id = event.chat_id
    sender_id = event.sender_id
    msg_id = event.id

    # 🔥 ДЕБАГ: логируем ВСЕ посты от авторов
    expected_author = MAIN_AUTHORS.get(group_id)
    if expected_author:
        logger.info(f'📨 POST: group={group_id}, sender={sender_id}/{expected_author}, msg={msg_id}')

    # только для указанных авторов
    if sender_id != expected_author:
        return

    # не отвечать себе
    if sender_id == MY_ID:
        return

    # auto-init
    if group_id not in last_comment_time:
        last_comment_time[group_id] = 0

    now = asyncio.get_event_loop().time()
    time_passed = now - last_comment_time[group_id]

    logger.info(f'⏱️  Group {group_id}: {time_passed:.0f}s passed (need {RATE_LIMIT_SECONDS})')

    # раз в 10 минут → комментируем
    if time_passed >= RATE_LIMIT_SECONDS:
        comment = random.choice(messages)
        try:
            await client.send_message(group_id, comment, reply_to=msg_id)
            last_comment_time[group_id] = now
            logger.info(f'✅ "{comment}" → group_{group_id} (msg {msg_id})')
        except ChatAdminRequiredError:
            logger.warning('❌ Нет прав в группе')
        except FloodWaitError as e:
            logger.warning(f'⏳ FloodWait {e.seconds}s')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f'❌ Send error: {e}')
    else:
        logger.debug(f'⏳ Skip: {time_passed:.0f}s < {RATE_LIMIT_SECONDS}s')


async def ping_telegram():
    """🔔 ANTI-SLEEP"""
    global telethon_alive
    while telethon_alive:
        try:
            await asyncio.sleep(300)
            await client.get_me()
            logger.debug('📡 Ping OK')
        except:
            logger.warning('📡 Ping FAIL')
            telethon_alive = False
            break


async def telethon_worker():
    """🔄 Перезапуск"""
    global MY_ID, telethon_alive, last_telethon_error, restart_count, ping_task

    while True:
        try:
            telethon_alive = False
            logger.info('🔄 Restarting Telethon...')

            await client.start()
            me = await client.get_me()
            MY_ID = me.id
            logger.info(f'🤖 @{me.username} ({MY_ID}) logged in')

            await get_channel_authors()
            telethon_alive = True
            last_telethon_error = None
            restart_count += 1

            ping_task = asyncio.create_task(ping_telegram())
            logger.info(f'🚀 ACTIVE | restarts: {restart_count} | authors: {MAIN_AUTHORS}')

            await client.run_until_disconnected()

        except Exception as e:
            telethon_alive = False
            last_telethon_error = str(e)
            logger.error(f'💥 Telethon crashed: {e}')

        if ping_task:
            ping_task.cancel()
        await asyncio.sleep(5)


async def main():
    logger.info('🎯 DEBUG Bot starting...')
    asyncio.create_task(telethon_worker())

    config = uvicorn.Config(
        app, host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        log_level="warning"
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == '__main__':
    import time  # для healthz
    asyncio.run(main())



