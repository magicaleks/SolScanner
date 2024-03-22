from scanner.scanner import Scanner
from telegram.client import TelegramBot

# tg = TelegramBot("6795829087:AAGX-GvhUBpYa0IhFp2hNLk6sMol1i2KBDw", "-2135735087")
tg = TelegramBot("6795829087:AAGX-GvhUBpYa0IhFp2hNLk6sMol1i2KBDw", "945482940")
# print(asyncio.run(tg.bot.get_chat("945482940")))

Scanner(tg).run()
