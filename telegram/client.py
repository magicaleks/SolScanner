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

    async def send(self, program: Program) -> None:
        if program.icon:
            await self.bot.send_photo(
                chat_id=self.channel,
                photo=URLInputFile(program.icon),
                caption=self._format_program(program),
                parse_mode="HTML",
            )
            try:
                await self.bot.send_photo(
                    chat_id="-2135735087",
                    photo=URLInputFile(program.icon),
                    caption=self._format_program(program),
                    parse_mode="HTML",
                )
            except:
                ...
        else:
            await self.bot.send_message(
                chat_id=self.channel,
                text=self._format_program(program),
                parse_mode="HTML",
            )
            try:
                await self.bot.send_message(
                    chat_id="-2135735087",
                    text=self._format_program(program),
                    parse_mode="HTML",
                )
            except:
                ...

    def _format_program(self, program: Program) -> str:
        text = ""
        if "unnamed" in program.title:
            text = f"<b>Coin:</b> <i>{program.title}</i> | <a href=\"{program.link}\">Solscan.io</a>\n"
        else:
            text = f"<b>Coin:</b> <code>{program.title}</code> | <a href=\"{program.link}\">Solscan.io</a>\n"
        
        text += f"<b>Address:</b> <code>{program.address}</code>"
        return text
