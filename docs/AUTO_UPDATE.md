# Автообновление из Git-репозитория

`scripts/auto_update.sh` проверяет удалённую ветку на новые коммиты и, если
они есть, подтягивает код (`git pull --ff-only`) и пересобирает/перезапускает
Docker-сервисы (`docker compose build && docker compose up -d`).

## Как это работает

1. `git fetch` — сравнивает локальный `HEAD` с `origin/<ветка>`.
2. Если коммиты совпадают — скрипт тихо завершается (`exit 0`), ничего не трогает.
3. Если есть новые коммиты:
   - проверяет, что в рабочей копии нет незакоммиченных изменений
     (если есть — останавливается, чтобы ничего не потерять);
   - `git pull --ff-only` (никаких merge/rebase — только чистое перемотка
     вперёд; если история разошлась, скрипт остановится с ошибкой, а не
     будет пытаться разрешать конфликты сам);
   - `docker compose build` + `docker compose up -d --remove-orphans`;
   - `docker image prune -f` (чистит старые неиспользуемые образы).
4. Всё пишется в `logs/auto_update.log`.
5. Если в `.env` заданы `TELEGRAM_BOT_TOKEN` и `AUTO_UPDATE_NOTIFY_CHAT_ID` —
   присылает уведомление об успехе/ошибке вам в Telegram.
6. Параллельные запуски исключены через `flock` (`.auto_update.lock`) — если
   предыдущий прогон ещё не закончился, новый просто выходит.

Скрипт написан на чистом bash (git/docker/curl) — не требует Python/venv,
поэтому работает даже если приложение сейчас не поднято.

## Настройка .env

```
AUTO_UPDATE_BRANCH=main
AUTO_UPDATE_NOTIFY_CHAT_ID=123456789   # ваш личный chat_id в Telegram (необязательно)
```

Как узнать свой `chat_id`: напишите что-нибудь боту
[@userinfobot](https://t.me/userinfobot) — он пришлёт ваш ID.

## Разовый запуск / проверка

```bash
cd /path/to/raffle-platform
./scripts/auto_update.sh
tail -f logs/auto_update.log
```

## Планирование через cron

```bash
crontab -e
```

Добавить строку (проверка каждые 5 минут):

```
*/5 * * * * /path/to/raffle-platform/scripts/auto_update.sh >> /path/to/raffle-platform/logs/cron.log 2>&1
```

## Планирование через systemd (рекомендуется для продакшена)

`/etc/systemd/system/raffle-auto-update.service`:

```ini
[Unit]
Description=Raffle Platform auto-update
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
WorkingDirectory=/path/to/raffle-platform
ExecStart=/path/to/raffle-platform/scripts/auto_update.sh
```

`/etc/systemd/system/raffle-auto-update.timer`:

```ini
[Unit]
Description=Проверять обновления Raffle Platform каждые 5 минут

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min
Persistent=true

[Install]
WantedBy=timers.target
```

Включить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now raffle-auto-update.timer
systemctl list-timers raffle-auto-update.timer
journalctl -u raffle-auto-update.service -f
```

## Важно

- Скрипт **не** трогает `.env` — секреты и локальные настройки на сервере
  остаются вашими, обновляется только код из репозитория.
- Если история сервера и `origin` разошлись (например, кто-то закоммитил
  прямо на проде) — скрипт остановится с ошибкой вместо того, чтобы
  автоматически сливать историю. Разбираться нужно вручную (`git status`,
  `git log`).
- Уровень доступа на сервере: репозиторий должен быть склонирован через
  протокол, для которого на сервере уже настроена аутентификация (SSH-ключ
  деплоя или сохранённый HTTPS-токен через `git credential.helper`) — сам
  скрипт учётные данные не хранит и не запрашивает.
