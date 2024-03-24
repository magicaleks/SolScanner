from aiogram import Bot
from aiogram.types import URLInputFile

from models.program import Program


class TelegramBot:
    """
    Telegram bot
    """

    bot: Bot
    channel: str

    def __init__(self, token: str, channel: str) -> None:
        self.bot = Bot(
            token=token,
        )
        self.channel = channel

    async def send(self, text: str, icon: str = "") -> None:
        if icon:
            await self.bot.send_photo(
                chat_id=self.channel,
                photo=URLInputFile(icon),
                caption=text,
                parse_mode="HTML",
            )
        else:
            await self.bot.send_message(
                chat_id=self.channel,
                text=text,
                parse_mode="HTML",
            )

    def _format_program(self, program: Program) -> str:
        text = ""
        if "unnamed" in program.title:
            text = f"<b>Coin:</b> <i>{program.title}</i> | <a href=\"{program.link}\">Solscan.io</a>\n"
        else:
            text = f"<b>Coin:</b> <code>{program.title}</code> | <a href=\"{program.link}\">Solscan.io</a>\n"
        
        text += f"<b>Address:</b> <code>{program.address}</code>\n"

        if program.symbol:
            text += f"<b>Symbol:</b> <code>{program.symbol}</code>\n"

        if program.description:
            text += f"<b>Sescription:</b> <code>{program.description}</code>\n"

        return text
