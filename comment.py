import os
import asyncio
import random
import logging
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import ChatAdminRequiredError, FloodWaitError, RPCError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

SESSION_STRING = "1BJWap1sBu5TKmL67ra0nnhqoyZzDIGlxtvZI7CFEGlHs3uZ4615SV5gLduhIbWh921RCtpi0wtVCTj7UtaM640EpBY3VEkpKU5GnETdz7Q3UyxPL6SS7INWHMBz5GmoNi4aTHL3SxypkUVoeIZG5TDBtmmveQhNQjfMGkNRZ_6Tr1Euc55MoHAAFf2rp9p2JwNTAqs33OQ29hy4WkiS_TzOedH5WHue2i5Utn-HsiIJdsygUMWz0NYARvkyaHUki475hAVyRBzhF0Q2IY10E172AHsHgwZw4LoZkZqSXk5modWCClKf-epd4ldqdzuEDkbmBucEQMMcARuLNWAHHc5SvlNQLgNQ="

messages = [
    'топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
    'лучший', 'интересно', '👍', 'огонь', 'как всегда на уровне'
]

API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

DISCUSSION_GROUPS = [-1001768427632, -1003304394138]
CHANNEL_GROUP_MAP = {-1001579090675: -1001768427632, -1003485053085: -1003304394138}

MAIN_AUTHORS = {}
last_commented_msg_id = {}  # group_id -> {msg_id: True}
last_comment_time = {}      # group_id -> timestamp
MY_ID = None
RATE_LIMIT_SECONDS = 1200

telethon_alive = False
last_telethon_error = None

@app.get("/healthz")
@app.get("/")
async def health():
    return {
        "status": "ok",
        "bot": "running",
        "groups": len(DISCUSSION_GROUPS),
        "authors": len(MAIN_AUTHORS),
        "telethon_alive": telethon_alive,
        "last_telethon_error": str(last_telethon_error) if last_telethon_error else None,
    }

async def get_channel_authors():
    for channel_id, group_id in CHANNEL_GROUP_MAP.items():
        try:
            async for msg in client.iter_messages(channel_id, limit=1):
                if msg.sender_id:
                    MAIN_AUTHORS[group_id] = msg.sender_id
                    last_commented_msg_id[group_id] = {}
                    last_comment_time[group_id] = 0
                    logger.info(f'Group {group_id}: author {msg.sender_id}')
                    break
        except Exception as e:
            logger.error(f'Channel {channel_id} error: {e}')

@client.on(events.NewMessage(chats=DISCUSSION_GROUPS))
async def handler(event):
    global MY_ID
    if MY_ID is None:
        return

    group_id = event.chat_id
    msg_id = event.id
    sender_id = event.sender_id

    if group_id not in MAIN_AUTHORS or sender_id != MAIN_AUTHORS[group_id]:
        return
    if sender_id == MY_ID:
        return

    group_comments = last_commented_msg_id.get(group_id, {})
    if msg_id in group_comments:
        return

    now = asyncio.get_event_loop().time()
    if now - last_comment_time.get(group_id, 0) < RATE_LIMIT_SECONDS:
        return

    comment = random.choice(messages)

    try:
        await client.send_message(group_id, comment, reply_to=msg_id)
        group_comments[msg_id] = True
        last_commented_msg_id[group_id] = group_comments
        last_comment_time[group_id] = now
        logger.info(f'Commented "{comment}" in {group_id} for msg {msg_id}')
    except ChatAdminRequiredError:
        logger.warning('No rights in chat')
    except FloodWaitError as e:
        logger.warning(f'FloodWait {e.seconds}s')
        await asyncio.sleep(e.seconds)
    except RPCError as e:
        logger.error(f'RPCError while sending: {e}')
    except Exception as e:
        logger.error(f'Unknown send error: {e}')

async def telethon_worker():
    global MY_ID, telethon_alive, last_telethon_error
    while True:
        try:
            telethon_alive = False
            logger.info("Starting Telethon client...")
            await client.start()
            me = await client.get_me()
            MY_ID = me.id
            logger.info(f'Logged in as @{me.username} ({MY_ID})')

            await get_channel_authors()
            telethon_alive = True
            last_telethon_error = None
            logger.info("Telethon is running, waiting until disconnected...")
            await client.run_until_disconnected()
            telethon_alive = False
            logger.warning("Telethon disconnected, will restart in 10s...")
        except Exception as e:
            telethon_alive = False
            last_telethon_error = e
            logger.error(f'Telethon crashed: {e}')
        # чтобы не крутить цикл слишком агрессивно
        await asyncio.sleep(10)

async def main():
    asyncio.create_task(telethon_worker())
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
