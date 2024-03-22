from scanner.scanner import Scanner
from telegram.client import TelegramBot

tg = TelegramBot("6795829087:AAGX-GvhUBpYa0IhFp2hNLk6sMol1i2KBDw", "-4123591573")

Scanner(tg).run()
