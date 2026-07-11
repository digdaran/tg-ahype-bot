"""
Покупка номерков: выбор розыгрыша (если их несколько) -> выбор количества ->
создание платежа -> ссылка СБП/платёжной страницы -> резервная проверка.
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.core.exceptions import GiveawayLockedError, ValidationError
from app.database import session_scope
from app.services.giveaway_service import GiveawayService
from app.services.payment_service import PaymentService
from bots.telegram.keyboards import (
    BTN_BUY,
    giveaways_keyboard,
    main_menu_keyboard,
    payment_link_keyboard,
    quantity_keyboard,
)
from bots.telegram.states import PurchaseStates
from bots.telegram.utils import require_participant

router = Router(name="purchase")

MAX_QUANTITY_OPTION = 20


@router.message(F.text == BTN_BUY)
async def start_purchase(message: Message, state: FSMContext) -> None:
    participant = await require_participant(message)
    if participant is None:
        return

    async with session_scope() as session:
        giveaways = await GiveawayService(session).list_open_for_participants()

    if not giveaways:
        await message.answer("Сейчас нет активных розыгрышей для покупки номерков. Загляните позже 🙏")
        return

    if len(giveaways) == 1:
        giveaway = giveaways[0]
        await state.update_data(giveaway_id=giveaway.id)
        await state.set_state(PurchaseStates.choosing_quantity)
        max_available = min(giveaway.tickets_remaining, MAX_QUANTITY_OPTION)
        await message.answer(
            f"Розыгрыш «{giveaway.name}»\nЦена номерка: {giveaway.ticket_price} ₽\n"
            f"Свободно номерков: {giveaway.tickets_remaining}\n\nСколько номерков купить?",
            reply_markup=quantity_keyboard(max_available),
        )
        return

    await state.set_state(PurchaseStates.choosing_giveaway)
    await message.answer(
        "Выберите розыгрыш:",
        reply_markup=giveaways_keyboard([(g.id, g.name) for g in giveaways]),
    )


@router.callback_query(F.data.startswith("giveaway:"))
async def choose_giveaway(callback: CallbackQuery, state: FSMContext) -> None:
    giveaway_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        giveaway = await GiveawayService(session).get(giveaway_id)

    if giveaway is None or giveaway.is_locked or not giveaway.is_registration_open:
        await callback.answer("Розыгрыш недоступен", show_alert=True)
        return

    await state.update_data(giveaway_id=giveaway.id)
    await state.set_state(PurchaseStates.choosing_quantity)
    max_available = min(giveaway.tickets_remaining, MAX_QUANTITY_OPTION)
    await callback.message.edit_text(
        f"Розыгрыш «{giveaway.name}»\nЦена номерка: {giveaway.ticket_price} ₽\n"
        f"Свободно номерков: {giveaway.tickets_remaining}\n\nСколько номерков купить?"
    )
    await callback.message.answer("Выберите количество:", reply_markup=quantity_keyboard(max_available))
    await callback.answer()


@router.callback_query(F.data.startswith("qty:"))
async def choose_quantity(callback: CallbackQuery, state: FSMContext) -> None:
    quantity = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    if not giveaway_id:
        await callback.answer("Сессия покупки истекла, начните заново", show_alert=True)
        return

    participant = await require_participant(callback.message)
    if participant is None:
        await callback.answer()
        return

    async with session_scope() as session:
        giveaway_service = GiveawayService(session)
        giveaway = await giveaway_service.get(giveaway_id)
        if giveaway is None:
            await callback.answer("Розыгрыш не найден", show_alert=True)
            return

        payment_service = PaymentService(session)
        try:
            payment = await payment_service.create_payment(participant, giveaway, quantity)
        except (ValidationError, GiveawayLockedError) as exc:
            await callback.answer(str(exc), show_alert=True)
            return

    await state.clear()
    await callback.message.edit_text(
        f"Заказ {payment.order_id}\nК оплате: {payment.amount} ₽ за {quantity} номерков.\n\n"
        "Нажмите кнопку ниже, чтобы перейти к оплате (СБП / платёжная страница). "
        "После оплаты номерки будут выданы автоматически."
    )
    await callback.message.answer(
        "Если платёж завершён, а номерки ещё не пришли — используйте резервную проверку:",
        reply_markup=payment_link_keyboard(payment.payment_url, payment.order_id),
    )
    await callback.answer()
