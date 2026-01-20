import os
import asyncio
import random
from fastapi import FastAPI
import uvicorn
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import ChatAdminRequiredError, FloodWaitError

app = FastAPI()

SESSION_STRING = "1BJWap1sBu5TKmL67ra0nnhqoyZzDIGlxtvZI7CFEGlHs3uZ4615SV5gLduhIbWh921RCtpi0wtVCTj7UtaM640EpBY3VEkpKU5GnETdz7Q3UyxPL6SS7INWHMBz5GmoNi4aTHL3SxypkUVoeIZG5TDBtmmveQhNQjfMGkNRZ_6Tr1Euc55MoHAAFf2rp9p2JwNTAqs33OQ29hy4WkiS_TzOedH5WHue2i5Utn-HsiIJdsygUMWz0NYARvkyaHUki475hAVyRBzhF0Q2IY10E172AHsHgwZw4LoZkZqSXk5modWCClKf-epd4ldqdzuEDkbmBucEQMMcARuLNWAHHc5SvlNQLgNQ="

messages = ['топ', '1', 'спасибо', '🔥', 'круто', 'благодарю']

client = TelegramClient(StringSession(SESSION_STRING), 23315051, '927ac8e4ddfc1092134b414b1a17f5bd')
DISCUSSION_GROUPS = [-1001768427632, -1003304394138]
MAIN_AUTHORS = {}
last_commented_msg_id = {}
MY_ID = None

@app.get("/healthz")
@app.get("/")
async def health():
    return {"status": "ok", "bot": "running 24/7"}

async def get_channel_authors():
    channel_groups = {
        -1001579090675: -1001768427632,
        -1003485053085: -1003304394138
    }
    for channel_id, group_id in channel_groups.items():
        try:
            async for msg in client.iter_messages(channel_id, limit=1):
                if msg.sender_id:
                    MAIN_AUTHORS[group_id] = msg.sender_id
                    last_commented_msg_id[group_id] = None
                    print(f'✅ Группа {group_id}: автор {msg.sender_id}')
                    break
        except Exception as e:
            print(f'❌ Канал {channel_id}: {e}')

@client.on(events.NewMessage(chats=DISCUSSION_GROUPS))
async def handler(event):
    global MY_ID
    group_id = event.chat_id
    msg_id = event.id
    sender_id = event.sender_id

    if group_id not in MAIN_AUTHORS or sender_id != MAIN_AUTHORS[group_id]:
        return
    if sender_id == MY_ID:
        return
    if last_commented_msg_id.get(group_id) == msg_id:
        return

    print(f'⚡ {msg_id} → {group_id}')
    comment = random.choice(messages)

    try:
        await client.send_message(group_id, comment, reply_to=msg_id)
        print(f'✅ "{comment}"!')
        last_commented_msg_id[group_id] = msg_id
    except ChatAdminRequiredError:
        print('❌ Нет прав')
    except FloodWaitError as e:
        print(f'⏳ {e.seconds}s')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        print(f'❌ {e}')

async def telethon_task():
    global MY_ID
    await client.start()
    me = await client.get_me()
    MY_ID = me.id
    print(f'🤖 @{me.username} (ID: {MY_ID}) ✅ SESSION OK!')
    await get_channel_authors()
    print(f'👥 Группы: {DISCUSSION_GROUPS}')
    print(f'📝 Авторы: {MAIN_AUTHORS}')
    print('⚡ МОЛНИЕНОСНЫЙ бот готов! 24/7 на Render!')
    await client.run_until_disconnected()

async def main():
    # Запуск Telethon task
    asyncio.create_task(telethon_task())
    
    # FastAPI на том же loop
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == '__main__':
    asyncio.run(main())
