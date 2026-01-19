import asyncio
import random
from telethon import TelegramClient, events
from telethon.errors import ChatAdminRequiredError, FloodWaitError, SessionPasswordNeededError

api_id = 23315051
api_hash = '927ac8e4ddfc1092134b414b1a17f5bd'
SESSION_NAME = 'clean_bot_2026'  # Новая чистая сессия

messages = ['топ', '1', 'спасибо', '🔥', 'круто', 'благодарю']

client = TelegramClient(SESSION_NAME, api_id, api_hash)

DISCUSSION_GROUPS = [-1001768427632, -1003304394138]
MAIN_AUTHORS = {}
last_commented_msg_id = {}


async def get_channel_authors():
    """Ищем авторов ТОЛЬКО после полной авторизации"""
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
    group_id = event.chat_id
    msg_id = event.id
    sender_id = event.sender_id

    # Только нужный автор
    if group_id not in MAIN_AUTHORS or sender_id != MAIN_AUTHORS[group_id]:
        return

    # Игнор своих сообщений (кешируем me)
    global MY_ID
    if sender_id == MY_ID:
        return

    # Только новый пост
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


async def main():
    global MY_ID

    # ✅ Авторизация 1 раз (сессия сохраняется!)
    await client.start()

    if not await client.is_user_authorized():
        print('🔐 Нужна авторизация (1 раз):')
        phone = input('Номер (+380...): ')
        sent = await client.send_code_request(phone)
        code = input('Код из Telegram app: ')
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            pw = input('2FA пароль: ')
            await client.sign_in(password=pw)
        print('✅ Авторизация завершена!')

    # Кешируем свой ID
    MY_ID = (await client.get_me()).id
    me = await client.get_me()
    print(f'🤖 @{me.username} (ID: {MY_ID})')

    # Ищем авторов
    await get_channel_authors()

    print(f'👥 Группы: {DISCUSSION_GROUPS}')
    print(f'📝 Авторы: {MAIN_AUTHORS}')
    print('⚡ МОЛНИЕНОСНЫЙ бот готов!')

    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
