from datetime import datetime, timedelta

from aiogram.types import (
    InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

import config

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Посмотреть не обработанные заказы"), KeyboardButton(text="Посмотреть отзывы")],
        [KeyboardButton(text="Заказы в пути"), KeyboardButton(text="Не в пути")],
        [KeyboardButton(text="Отправить рассылку")]
    ], resize_keyboard=True
)


# ------------------ФУНКЦИЯ ДОБАВЛЕНИЯ КЛАВИАТУРЫ ВЫБОРА ВРЕМЕНИ---------------------#
def get_delivery_time_buttons():
    now = datetime.now()
    today_end = now.replace(hour=19, minute=0, second=0, microsecond=0)
    tomorrow_start = today_end + timedelta(hours=15)

    buttons = {
        "Как можно быстрее": "time_Как можно быстрее"
    }

    for i in range(10, 20):
        if now.hour < i:
            buttons[f"Сегодня {i}:00"] = f"time_Сегодня в {i}:00"
        buttons[f"Завтра {i}:00"] = f"time_Завтра в {i}:00"

    return buttons


def get_callback_btns(*, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()


def get_delivery_time_keyboard():
    delivery_time_buttons = get_delivery_time_buttons()
    return get_callback_btns(btns=delivery_time_buttons, sizes=(2,))


def orders_markup(orders):
    markup = InlineKeyboardBuilder()

    markup.add(
        InlineKeyboardButton(text="За текущую неделю", callback_data="this_week"),
        InlineKeyboardButton(text="За текущий месяц", callback_data="this_month"),
        InlineKeyboardButton(text="За сегодня", callback_data="today")
    )

    return markup


support_rm = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Связаться с поддержкой", url=f"tg://resolve?domain={config.FEED_BACK_USERNAME}")]
])

user_kb = ReplyKeyboardBuilder()
user_kb.row(KeyboardButton(
    text="Заказать воду")
)
user_kb.row(KeyboardButton(text="Запустить бота"), KeyboardButton(text="Инструкция"), KeyboardButton(text="Поддержка"))


def build_info_kb() -> InlineKeyboardMarkup:
    tg_channel_btn = InlineKeyboardButton(
        text="Канал",
        url="https://t.me/classabstract?subscribe=True"
    )
    rows = [
        [tg_channel_btn]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    return markup
