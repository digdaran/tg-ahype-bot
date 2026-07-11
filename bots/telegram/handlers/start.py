"""
Регистрация участника: подтверждение телефона и привязка Telegram ID
к существующей записи участника (главный идентификатор — номер телефона).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.core.exceptions import ValidationError
from app.database import session_scope
from app.services.registration_service import RegistrationService
from bots.telegram.keyboards import BTN_SHARE_PHONE, main_menu_keyboard, phone_request_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with session_scope() as session:
        service = RegistrationService(session)
        participant = await service.find_by_telegram_id(message.from_user.id)

    if participant:
        await message.answer(
            f"С возвращением, {participant.full_name or participant.phone}! 👋\n"
            "Выберите действие в меню ниже.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        "Добро пожаловать в бот розыгрышей цифровых постеров! 🎨\n\n"
        "Чтобы продолжить, подтвердите номер телефона — это ваш главный "
        "идентификатор как участника розыгрыша.\n\n"
        f"Нажмите «{BTN_SHARE_PHONE}» ниже.",
        reply_markup=phone_request_keyboard(),
    )


@router.message(F.contact)
async def handle_contact(message: Message) -> None:
    if message.contact.user_id and message.contact.user_id != message.from_user.id:
        await message.answer("Пожалуйста, отправьте свой собственный контакт с помощью кнопки ниже.")
        return

    phone = message.contact.phone_number
    async with session_scope() as session:
        service = RegistrationService(session)
        try:
            participant = await service.link_telegram(
                phone=phone,
                telegram_user_id=message.from_user.id,
                telegram_username=message.from_user.username,
            )
        except ValidationError as exc:
            await message.answer(f"⚠️ {exc}")
            return

    await message.answer(
        "Телефон подтверждён ✅\n\nТеперь вам доступны покупка номерков, просмотр своих номерков и истории покупок.",
        reply_markup=main_menu_keyboard(),
    )
