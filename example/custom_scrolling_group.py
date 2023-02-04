import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram_dialog import (
    Dialog,
    DialogManager,
    DialogRegistry,
    StartMode,
    Window,
)
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup
from aiogram_dialog.widgets.kbd.scrolling_group import PrevPage, NextPage, CurrentPage
from aiogram_dialog.widgets.text import Const, Format

API_TOKEN = "5450610003:AAFi6CYOPeLnjmclo8uVmFFtjrtTcSlQkYI"


class DialogSG(StatesGroup):
    love = State()


async def start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(DialogSG.love, mode=StartMode.RESET_STACK)


def get_love_buttons():
    i_love_ad = "I love aiogram_dialog with all my heart and beyond."
    i_love_ad = i_love_ad.split()

    keyboard = []

    for i, word in enumerate(i_love_ad):
        keyboard.append(Button(text=Const(word), id=f"love_{i}"))

    return keyboard


love_buttons = get_love_buttons()

dialog = Dialog(
    Window(
        Const("All my hommies use <code>aiogram_dialog</code> with their bots 🤙"),
        ScrollingGroup(
            *love_buttons,
            id="love_buttons",
            width=1,
            height=3,
            pager_template=[
                PrevPage(Const("<<")),
                CurrentPage(Format("{__value__}")),
                NextPage(Const(">>")),
            ],
        ),
        state=DialogSG.love,
        parse_mode="HTML",
    )
)


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    storage = MemoryStorage()
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=storage)
    dp.message.register(start, F.text == "/start")

    registry = DialogRegistry(dp)
    registry.register(dialog)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
