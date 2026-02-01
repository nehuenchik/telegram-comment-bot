import asyncio
import random
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# Минимальные логи для сервера
logging.basicConfig(level=logging.WARNING, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

# НАСТРОЙКИ
SESSION_STRING = "1BJWap1sBu4M7Og_xKvAXSrpZToA_HUSt0zWVZjrHjqZdrZYGEPS5jmjF1BzfIqs9X441k1Io11fKFT25ak5xs0xU88n1s8LGt0eBgL1VGzvAB3lGoLM2XzPmKhMxbiH3sVHfPQuskuyq4pFAX8VzW8zPSQITJRXNlPuE5gYcVZ0oBCprvQTyuoTNO5hoDB5YJC3nqfaewlIGn1bLKLnWdNLU5WKDL30ohi2s0T_gkjhh5HedgnVX5RhtUvT9XODvY8ALVb0gAGrL_tibtuM4KP7szziTfoITvDbcqm0wh2VYdF0l6Px1GMzwjcNiESBCBOW4BG5GVsCyj44bAeId9tPd5MtDNKs="
API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

GROUPS = [
    -1001768427632,  # Группа 1
    -1003304394138  # Группа 2 (Hui)
]

RATE_LIMIT_SECONDS = 600  # 10 минут на группу
messages = ['топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
    'лучший', 'интересно', '👍', 'огонь', 'супер', 'отлично',
    '👌', 'спс', 'класно', 'первый', 'о']

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
last_comment_time = {group: 0 for group in GROUPS}
MY_ID = None


@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    global last_comment_time, MY_ID

    group_id = event.chat_id

    if MY_ID is None:
        me = await client.get_me()
        MY_ID = me.id

    # Пропускаем свои посты
    if event.sender_id == MY_ID:
        return

    now = asyncio.get_event_loop().time()
    time_passed = now - last_comment_time[group_id]

    if time_passed >= RATE_LIMIT_SECONDS:
        # Задержка 1-3 сек
        await asyncio.sleep(random.uniform(1, 3))

        comment = random.choice(messages)
        try:
            sent = await client.send_message(group_id, comment, reply_to=event.id)
            last_comment_time[group_id] = now
            logger.info(f'✅ {group_id} | "{comment}" #{sent.id}')
        except FloodWaitError as e:
            logger.warning(f'⏳ {group_id} | {e.seconds}s')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f'❌ {group_id} | {e}')

    # Тихо пропускаем (без спама логов)


async def main():
    await client.start()
    logger.info(f'🤖 АКТИВЕН: {len(GROUPS)} групп')

    # Тихий тест (без сообщений)
    for group in GROUPS:
        try:
            await client.get_entity(group)
        except:
            logger.error(f'❌ Нет доступа: {group}')

    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🛑 Стоп')

