"""
Клавиатуры VK-бота.

Постоянная (persistent) не-inline клавиатура — главное меню (аналог
ReplyKeyboard в Telegram): нажатие на Text-кнопку отправляет обычное
сообщение с текстом кнопки. Inline-клавиатуры (Callback) используются
только там, где действительно нужны быстрые действия без отправки
нового сообщения: выбор количества номерков, розыгрыша, резервная проверка.
"""
from __future__ import annotations

from vkbottle import Callback, Keyboard, KeyboardButtonColor, OpenLink, Text

BTN_BUY = "🎫 Купить номерки"
BTN_MY_TICKETS = "📋 Мои номерки"
BTN_HISTORY = "🧾 История покупок"
BTN_CHECK_PAYMENT = "🔄 Проверить оплату"
BTN_HELP = "❓ Помощь"


def main_menu_keyboard() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(Text(BTN_BUY))
    kb.row()
    kb.add(Text(BTN_MY_TICKETS))
    kb.add(Text(BTN_HISTORY))
    kb.row()
    kb.add(Text(BTN_CHECK_PAYMENT))
    kb.add(Text(BTN_HELP))
    return kb.get_json()


def giveaways_keyboard(giveaways: list[tuple[str, str]]) -> str:
    kb = Keyboard(inline=True)
    for i, (gid, name) in enumerate(giveaways):
        if i:
            kb.row()
        kb.add(Callback(name, payload={"cmd": "giveaway", "id": gid}))
    return kb.get_json()


def quantity_keyboard(giveaway_id: str, max_available: int) -> str:
    options = [o for o in [1, 2, 3, 5, 10] if o <= max_available] or [max_available]
    kb = Keyboard(inline=True)
    for i, o in enumerate(options):
        if i and i % 3 == 0:
            kb.row()
        kb.add(Callback(str(o), payload={"cmd": "qty", "giveaway_id": giveaway_id, "qty": o}))
    return kb.get_json()


def payment_link_keyboard(payment_url: str, order_id: str) -> str:
    kb = Keyboard(inline=True)
    kb.add(OpenLink(payment_url, "💳 Перейти к оплате / СБП"))
    kb.row()
    kb.add(Callback("🔄 Проверить оплату", payload={"cmd": "check", "order_id": order_id}))
    return kb.get_json()
