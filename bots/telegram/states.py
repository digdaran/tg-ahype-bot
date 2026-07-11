"""Состояния FSM Telegram-бота."""
from aiogram.fsm.state import State, StatesGroup


class PurchaseStates(StatesGroup):
    choosing_giveaway = State()
    choosing_quantity = State()
