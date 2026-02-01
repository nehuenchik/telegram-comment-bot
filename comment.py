#!/usr/bin/env python3
# Telegram Comment Bot - Render Background Worker Fix
# Комментирует ТОЛЬКО forwarded посты от каналов в указанные группы
# ✅ Логи видны в Render сразу!

import asyncio
import random
import logging
import sys
import os

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ✅ ФИКС Render: принудительный вывод логов в stdout
os.environ['PYTHONUNBUFFERED'] = '1'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)
logger = logging.getLogger(__name__)

SESSION_STRING = "1BJWap1wBux2jgHDja76evZiaiSp4ZjoGGb_biQVh9kOdYBKm9LKqKoSt-XhtAxMcE7DjErX53ntwQDfRzzCuKsp7BLcRClCQOSNdA0pYY7sHg4gbirA62RdD0gXVEe7yIWLVCdcBgdJTYq__IEgL3WKyN7IDchaxD2skwH6CaVAAMJVqEevsS53fxT6SrkxtM1LxmLPP8Wip2Jt_P0MzbhDozIAerFoituBlXuBFCLHQA8wG8aL-rUwv3H-5G9wxmE4onxhHr4RdowNfewnaPTQPgzYNZajLuxt-O53kdm0FFHB-_Se6Uc_G5LfiumSMLWay2XeB7mXaNTwVwzvwq4I4Kgm-12M="
API_ID = 23315051
API_HASH = '927ac8e4ddfc1092134b414b1a17f5bd'

TARGET_CHANNELS = [1579090675, 3485053085]  # ✅ 2 канала!
GROUPS = [-1001768427632, -1003304394138]  # ✅ 2 группы!

RATE_LIMIT_SECONDS = 600
messages = ['топ', '1', 'спасибо', '🔥', 'круто', 'благодарю',
            'лучший', 'интересно', '👍', 'огонь', 'супер', 'отлично',
            '👌', 'спс', 'класно', 'первый', 'о']

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
last_comment_time = 0  # Общий рейт-лимит
MY_ID = None
recent_msgs = set()  # Защита от дублирования


@client.on(events.NewMessage(chats=GROUPS))
async def handler(event):
    global last_comment_time, MY_ID, recent_msgs

    msg_id = event.id

    # ✅ Антидубликат (1 запрос на пост)
    if msg_id in recent_msgs:
        return
    recent_msgs.add(msg_id)

    # ✅ Только forwarded
    if not event.forward:
        return

    # ✅ Только нужные каналы
    forward_channel = getattr(event.forward.from_id, 'channel_id', None)
    if forward_channel not in TARGET_CHANNELS:
        return

    if MY_ID is None:
        MY_ID = (await client.get_me()).id

    now = asyncio.get_event_loop().time()
    time_passed = now - last_comment_time

    if time_passed >= RATE_LIMIT_SECONDS:
        # МГНОВЕННО! Без задержки
        comment = random.choice(messages)
        try:
            sent = await client.send_message(event.chat_id, comment, reply_to=event.id)
            last_comment_time = now
            logger.info(f'✅ {comment} под постом #{msg_id}')
        except FloodWaitError as e:
            logger.warning(f'⏳ FloodWait {e.seconds}s')
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f'❌ Ошибка отправки: {e}')
    else:
        logger.debug(f'⏳ Рейт-лимит, осталось {RATE_LIMIT_SECONDS - time_passed:.0f}s')


async def main():
    await client.start()
    logger.info(f'🤖 АКТИВЕН: каналы {TARGET_CHANNELS} → группы {GROUPS}')

    # Проверка доступа
    for group in GROUPS:
        try:
            await client.get_entity(group)
            logger.info(f'✅ Доступ к группе {group}')
        except Exception as e:
            logger.error(f'❌ Нет доступа к {group}: {e}')

    # Healthcheck каждые 5 мин
    async def heartbeat():
        while True:
            await asyncio.sleep(300)
            logger.info('🟢 Bot alive - слушает сообщения')

    asyncio.create_task(heartbeat())
    await client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('🛑 Stopped by user')
    except Exception as e:
        logger.error(f'❌ Критическая ошибка: {e}')


