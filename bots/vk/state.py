"""
Минимальное состояние процесса VK-бота: кто сейчас должен прислать номер
телефона текстом (у VK нет нативной кнопки «поделиться контактом», как в
Telegram, поэтому телефон запрашивается и подтверждается текстом).

Хранится в памяти процесса — этого достаточно для одного инстанса бота.
Если потребуется горизонтальное масштабирование VK-бота на несколько
процессов, следует заменить на встроенный state_dispenser vkbottle
(BuiltinStateDispenser) или на Redis.
"""
from __future__ import annotations

_awaiting_phone: set[int] = set()


def mark_awaiting_phone(vk_user_id: int) -> None:
    _awaiting_phone.add(vk_user_id)


def is_awaiting_phone(vk_user_id: int) -> bool:
    return vk_user_id in _awaiting_phone


def clear_awaiting_phone(vk_user_id: int) -> None:
    _awaiting_phone.discard(vk_user_id)
