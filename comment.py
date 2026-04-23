import asyncio
import random
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('comment_bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

SESSION_STRING = "1BJWap1sBuwNPad10w2ahWs0fcaiuHgOxzHjivZVzTdCwNCqHcMlqV8Fzj5XFY8kBEpqE6wP5NpCd8RwvRLjCJiQbqO3ma2Q0be0eRUq9N04_k4wh3niqjYKOr3VNRXd_e81zMc-2CvNT-HQL8yRCtE7nb0HGoleWfLFM7BINKtjaiiP6KbYsPc0mdliqKX_ujIolXJRKnT4QOxUMorWwhYhnoq8XNGnKhIXrWWnajInDT6FrP40rJZzn3VHHcPPrnQvY5W78d1G4_G2a5D__fMrR4NBv672s5nsgcpoCeDlm25rKrAHOMytGWXN85xILhtSHYC3uXSk52YHC_ArVGa4C71sjV7w="
API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

TARGET_CHANNELS = [1579090675, 3761987891]
GROUPS = [-1001768427632, -1003937746434]

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

    msg_key = (event.chat_id, event.id)

    if msg_key in recent_msgs:
        return
    recent_msgs.add(msg_key)

    if not event.forward:
        return

    forward_channel = getattr(event.forward.from_id, 'channel_id', None)
    if forward_channel not in TARGET_CHANNELS:
        return

    if MY_ID is None:
        MY_ID = (await client.get_me()).id
        logger.info(f'Авторизован аккаунт ID={MY_ID}')

    now = asyncio.get_event_loop().time()
    time_passed = now - last_comment_time

    if time_passed >= RATE_LIMIT_SECONDS:
        comment = random.choice(messages)

        try:
            sent = await client.send_message(event.chat_id, comment, reply_to=event.id)
            last_comment_time = now
            logger.info(
                f'Комментарий отправлен: group={event.chat_id}, '
                f'post_id={event.id}, comment_id={sent.id}, text="{comment}"'
            )
        except FloodWaitError as e:
            logger.warning(f'FloodWait: sleep {e.seconds}s')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f'Ошибка отправки комментария: {e}')
    else:
        logger.info(
            f'Рейт-лимит активен: group={event.chat_id}, '
            f'post_id={event.id}, wait_left={int(RATE_LIMIT_SECONDS - time_passed)}s'
        )


async def main():
    await client.start()
    logger.info(f'Бот запущен. Каналы={TARGET_CHANNELS}, группы={GROUPS}')

    for group in GROUPS:
        try:
            entity = await client.get_entity(group)
            logger.info(f'Доступ к группе есть: {group} | {entity.title}')
        except Exception as e:
            logger.error(f'Ошибка доступа к группе {group}: {e}')

    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Остановка по Ctrl+C')

