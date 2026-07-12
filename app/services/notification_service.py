"""
Уведомления участников после успешной ОНЛАЙН-оплаты: список выданных номерков
+ цифровой постер. Отправляется напрямую через Telegram/VK Bot API, независимо
от того, запущен ли в данный момент процесс соответствующего бота.

При ручной (офлайн) продаже уведомления не отправляются — постер физический,
выдаётся оператором лично (это уже гарантируется тем, что этот сервис
вызывается только из PaymentService, а не из ManualRegistrationService).

Если интеграция выключена (TELEGRAM_ENABLED=false / VK_ENABLED=false в .env —
см. app/config.py), отправка через соответствующий канал пропускается, даже
если у участника есть привязанный telegram_user_id / vk_user_id.
"""
from __future__ import annotations

from app.config import get_settings
from app.integrations import telegram_api, vk_api
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.models.ticket import Ticket

settings = get_settings()


class NotificationService:
    @staticmethod
    def _build_text(giveaway: Giveaway, tickets: list[Ticket]) -> str:
        codes = "\n".join(f"🎟 <b>{t.full_code}</b>" for t in tickets)
        return (
            f"✅ Оплата подтверждена!\n\n"
            f"Розыгрыш: <b>{giveaway.name}</b>\n"
            f"Ваши номерки ({len(tickets)} шт.):\n{codes}\n\n"
            f"Спасибо за покупку! Цифровой постер прикреплён."
        )

    async def notify_online_purchase(self, participant: Participant, giveaway: Giveaway, tickets: list[Ticket]) -> None:
        text = self._build_text(giveaway, tickets)

        if settings.telegram_enabled and participant.telegram_user_id:
            if giveaway.digital_poster_file_id:
                sent = await telegram_api.send_photo(
                    participant.telegram_user_id, giveaway.digital_poster_file_id, caption=text
                )
                if not sent:
                    await telegram_api.send_message(participant.telegram_user_id, text)
            else:
                await telegram_api.send_message(participant.telegram_user_id, text)

        if settings.vk_enabled and participant.vk_user_id:
            plain_text = text.replace("<b>", "").replace("</b>", "")
            await vk_api.send_message(participant.vk_user_id, plain_text)
