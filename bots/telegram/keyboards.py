"""
Клавиатуры Telegram-бота.

По требованиям: постоянное ReplyKeyboard-меню внизу экрана (mobile-first),
inline-кнопки — только там, где это действительно необходимо (выбор
количества номерков, способ оплаты, ссылка на оплату, резервная проверка).
"""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

BTN_BUY = "🎫 Купить номерки"
BTN_MY_TICKETS = "📋 Мои номерки"
BTN_HISTORY = "🧾 История покупок"
BTN_CHECK_PAYMENT = "🔄 Проверить оплату"
BTN_HELP = "❓ Помощь"
BTN_SHARE_PHONE = "📱 Отправить номер телефона"


def phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SHARE_PHONE, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BUY)],
            [KeyboardButton(text=BTN_MY_TICKETS), KeyboardButton(text=BTN_HISTORY)],
            [KeyboardButton(text=BTN_CHECK_PAYMENT), KeyboardButton(text=BTN_HELP)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def quantity_keyboard(max_available: int) -> InlineKeyboardMarkup:
    options = [1, 2, 3, 5, 10]
    options = [o for o in options if o <= max_available] or [max_available]
    rows = [
        [InlineKeyboardButton(text=str(o), callback_data=f"qty:{o}") for o in options[i:i + 3]]
        for i in range(0, len(options), 3)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_link_keyboard(payment_url: str, order_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Перейти к оплате / СБП", url=payment_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check:{order_id}")],
        ]
    )


def giveaways_keyboard(giveaways: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    """giveaways: список (id, название)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=name, callback_data=f"giveaway:{gid}")] for gid, name in giveaways]
    )
