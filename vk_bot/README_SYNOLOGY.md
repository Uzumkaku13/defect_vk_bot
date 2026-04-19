# Развертывание на Synology NAS

## 1. Что нужно на NAS
- DSM 7.2+ и пакет **Container Manager**.
- Общая папка, например `/volume1/docker/tehnokom-vk-bot`.

## 2. Что скопировать
Скопируйте весь проект в папку NAS, например:
`/volume1/docker/tehnokom-vk-bot`

Структура после копирования:
- `docker-compose.yml`
- `Dockerfile`
- `.env`
- `assets/`
- `fonts/`
- `data/`

## 3. Шрифты Times New Roman
Если нужен именно Times New Roman, вручную положите в папку `fonts/` ваши легально полученные файлы:
- `times.ttf`
- `timesbd.ttf`
- `timesi.ttf`
- `timesbi.ttf`

Если папка `fonts/` пустая, проект автоматически переключится на `DejaVu Serif` с поддержкой кириллицы.

## 4. .env
Пример:

```env
VK_TOKEN=vk1.a.xxx
GROUP_ID=123456789
DB_PATH=data/bot_data.sqlite3
DOCS_DIR=data/generated_docs
MEDIA_DIR=data/media
ASSETS_DIR=assets
FONTS_DIR=fonts
LOGO_PATH=assets/tehnokom_placeholder.png
LOG_LEVEL=INFO
```

## 5. Первый запуск через Container Manager
### Вариант A: через UI проекта
1. Откройте **Container Manager**.
2. Перейдите в **Project**.
3. Нажмите **Create**.
4. Выберите папку проекта.
5. Подтяните `docker-compose.yml`.
6. Запустите проект.

### Вариант B: через SSH
```bash
cd /volume1/docker/tehnokom-vk-bot
sudo docker compose up -d --build
```

## 6. Инициализация БД
При первом запуске один раз выполните:
```bash
sudo docker compose exec vk_bot python init_db.py
```

## 7. Обновление
```bash
cd /volume1/docker/tehnokom-vk-bot
sudo docker compose down
sudo docker compose up -d --build
```

## 8. Где лежат данные
- PDF: `data/generated_docs/`
- фото: `data/media/`
- база: `data/bot_data.sqlite3`

## 9. Диагностика
Логи:
```bash
sudo docker compose logs -f vk_bot
```
