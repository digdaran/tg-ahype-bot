# Резервное копирование базы данных

Скрипт `scripts/backup_db.sh` снимает консистентный дамп SQLite (проект
поддерживает только SQLite, см. README раздел «База данных»), сжимает его
и удаляет бэкапы старше `BACKUP_RETENTION_DAYS`.

## Настройка (`.env`)

```
BACKUP_DIR=./backups              # куда складывать бэкапы (вне docker volume с БД!)
BACKUP_RETENTION_DAYS=14          # сколько дней хранить
```

Важно: `BACKUP_DIR` должен быть **вне** volume `sqlite_data` — если
контейнер/volume с БД будет потерян, бэкапы, лежащие внутри того же тома,
потеряются вместе с ним.

## Как это работает

- Используется `sqlite3 ... "VACUUM INTO 'файл'"` — атомарный консистентный
  снимок, снимается без остановки backend'а и без риска зацепить файл в
  процессе записи (в отличие от простого `cp`). Если `sqlite3` CLI не
  установлен на хосте — скрипт делает обычную копию файла (с предупреждением
  в лог) как fallback.
- Итоговый файл сжимается (`gzip`).
- Бэкапы старше `BACKUP_RETENTION_DAYS` удаляются автоматически при каждом
  запуске.
- Лог пишется в `logs/backup.log`.
- Если `DATABASE_URL` указывает не на SQLite — скрипт завершится с понятной
  ошибкой (PostgreSQL не поддерживается).

## Ручной запуск / проверка

```bash
./scripts/backup_db.sh
ls -la backups/
```

## Восстановление

```bash
gunzip -k backups/db_20260101_120000.sqlite3.gz
# Остановите backend/бота перед подменой файла БД, иначе рискуете гонкой:
docker compose stop backend telegram-bot
cp backups/db_20260101_120000.sqlite3 data/db.sqlite3   # путь внутри volume sqlite_data
docker compose start backend telegram-bot
```

## Автоматизация по расписанию

### cron

```bash
crontab -e
```
```
# Ежедневно в 03:15
15 3 * * * /path/to/raffle_platform/scripts/backup_db.sh >> /path/to/raffle_platform/logs/cron_backup.log 2>&1
```

### systemd (таймер)

`/etc/systemd/system/raffle-backup.service`:
```ini
[Unit]
Description=Raffle Platform - резервное копирование БД

[Service]
Type=oneshot
WorkingDirectory=/path/to/raffle_platform
ExecStart=/path/to/raffle_platform/scripts/backup_db.sh
```

`/etc/systemd/system/raffle-backup.timer`:
```ini
[Unit]
Description=Ежедневный бэкап БД Raffle Platform

[Timer]
OnCalendar=*-*-* 03:15:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now raffle-backup.timer
```

## Важно

- Скрипт **не** трогает `.env` и не подключается к БД для записи — только
  читает/копирует.
- Если файл БД не найден или `DATABASE_URL` не SQLite, скрипт завершится с
  ошибкой и понятным сообщением в лог — тихого "успеха" без реального
  бэкапа не бывает.
- Периодически проверяйте, что восстановление из бэкапа реально работает
  (см. раздел выше) — бэкап, который ни разу не восстанавливали, нельзя
  считать надёжным.
