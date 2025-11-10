# 🚀 Инструкции по деплою ChatQuestBot

## 📋 Содержание

1. [Heroku](#heroku)
2. [Railway](#railway)
3. [Render](#render)
4. [Docker](#docker)
5. [VPS (Ubuntu)](#vps-ubuntu)
6. [Telegram Bot API Server](#telegram-bot-api-server)

---

## 🔧 Подготовка

Перед деплоем убедитесь, что у вас есть:

✅ `BOT_TOKEN` от @BotFather
✅ `CHAT_ID` вашей группы
✅ `OPERATOR_IDS` (ваш Telegram ID)

---

## 1️⃣ Heroku

### Быстрый деплой:

```bash
# 1. Установите Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# 2. Войдите в Heroku
heroku login

# 3. Создайте приложение
heroku create your-bot-name

# 4. Установите переменные окружения
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set CHAT_ID=your_chat_id
heroku config:set OPERATOR_IDS=your_operator_ids

# 5. Задеплойте
git push heroku main

# 6. Запустите бота
heroku ps:scale web=1

# 7. Проверьте логи
heroku logs --tail
```

### Через веб-интерфейс:

1. Зайдите на [heroku.com](https://heroku.com)
2. Создайте новое приложение
3. Подключите GitHub репозиторий
4. В Settings → Config Vars добавьте:
   - `BOT_TOKEN`
   - `CHAT_ID`
   - `OPERATOR_IDS`
5. Deploy → Deploy Branch

---

## 2️⃣ Railway

### Деплой через Railway:

1. Зайдите на [railway.app](https://railway.app)
2. Нажмите "New Project" → "Deploy from GitHub repo"
3. Выберите ваш репозиторий
4. В Variables добавьте:
   ```
   BOT_TOKEN=ваш_токен
   CHAT_ID=id_чата
   OPERATOR_IDS=ваши_ids
   ```
5. Railway автоматически задеплоит бота

### Через CLI:

```bash
# 1. Установите Railway CLI
npm i -g @railway/cli

# 2. Войдите
railway login

# 3. Инициализируйте проект
railway init

# 4. Добавьте переменные
railway variables set BOT_TOKEN=your_token
railway variables set CHAT_ID=your_chat_id
railway variables set OPERATOR_IDS=your_ids

# 5. Задеплойте
railway up
```

---

## 3️⃣ Render

1. Зайдите на [render.com](https://render.com)
2. New → Web Service
3. Подключите GitHub репозиторий
4. Настройки:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. В Environment добавьте переменные:
   ```
   BOT_TOKEN=ваш_токен
   CHAT_ID=id_чата
   OPERATOR_IDS=ваши_ids
   ```
6. Create Web Service

---

## 4️⃣ Docker

### Локально:

```bash
# 1. Соберите образ
docker build -t chatquest-bot .

# 2. Запустите контейнер
docker run -d \
  --name chatquest-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  chatquest-bot

# 3. Проверьте логи
docker logs -f chatquest-bot

# 4. Остановить
docker stop chatquest-bot

# 5. Удалить
docker rm chatquest-bot
```

### С Docker Compose:

```bash
# 1. Запустите
docker-compose up -d

# 2. Проверьте статус
docker-compose ps

# 3. Логи
docker-compose logs -f

# 4. Остановить
docker-compose down

# 5. Перезапустить
docker-compose restart
```

---

## 5️⃣ VPS (Ubuntu)

### Установка на сервер:

```bash
# 1. Подключитесь к серверу
ssh user@your-server-ip

# 2. Обновите систему
sudo apt update && sudo apt upgrade -y

# 3. Установите Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip git -y

# 4. Клонируйте репозиторий
git clone https://github.com/your-username/she_codes_bot.git
cd she_codes_bot

# 5. Создайте виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# 6. Установите зависимости
pip install -r requirements.txt

# 7. Настройте .env
nano .env
# Вставьте ваши данные и сохраните (Ctrl+X, Y, Enter)

# 8. Проверьте конфигурацию
python test_config.py

# 9. Запустите бота
python main.py
```

### Запуск как сервис (systemd):

```bash
# 1. Создайте файл сервиса
sudo nano /etc/systemd/system/chatquest-bot.service
```

Вставьте:

```ini
[Unit]
Description=ChatQuest Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/she_codes_bot
Environment="PATH=/home/your-username/she_codes_bot/venv/bin"
ExecStart=/home/your-username/she_codes_bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Перезагрузите systemd
sudo systemctl daemon-reload

# 3. Запустите сервис
sudo systemctl start chatquest-bot

# 4. Включите автозапуск
sudo systemctl enable chatquest-bot

# 5. Проверьте статус
sudo systemctl status chatquest-bot

# 6. Просмотр логов
sudo journalctl -u chatquest-bot -f

# Управление сервисом:
sudo systemctl stop chatquest-bot      # Остановить
sudo systemctl restart chatquest-bot   # Перезапустить
sudo systemctl status chatquest-bot    # Статус
```

---

## 6️⃣ Telegram Bot API Server

Для работы через собственный сервер Telegram Bot API:

1. Поднимите [telegram-bot-api](https://github.com/tdlib/telegram-bot-api)
2. В `config.py` измените:

```python
# Вместо стандартного API
bot = Bot(
    token=Config.BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        api_server="http://your-server:8081"  # Ваш API сервер
    )
)
```

---

## 🔒 Безопасность при деплое

⚠️ **Важно:**

1. **Никогда не коммитьте `.env` в Git!**
   ```bash
   # Убедитесь, что .env в .gitignore
   echo ".env" >> .gitignore
   ```

2. **Используйте переменные окружения**
   - Все токены и ID храните в Environment Variables
   - Не храните секреты в коде

3. **Регулярные бэкапы**
   ```bash
   # Настройте автоматический бэкап базы
   cp data/bot.db data/bot.db.backup
   ```

4. **Логи**
   - Регулярно проверяйте `bot.log`
   - Настройте ротацию логов

---

## 📊 Мониторинг

### Проверка работоспособности:

```bash
# Локально
python test_config.py

# На сервере
tail -f bot.log

# Docker
docker logs -f chatquest-bot

# Systemd
sudo journalctl -u chatquest-bot -f
```

### Полезные команды:

```bash
# Размер базы данных
du -h data/bot.db

# Количество пользователей
sqlite3 data/bot.db "SELECT COUNT(*) FROM users;"

# Топ-5 участников
python view_stats.py
```

---

## 🆘 Решение проблем

### Бот не запускается:

```bash
# 1. Проверьте конфигурацию
python test_config.py

# 2. Проверьте логи
cat bot.log

# 3. Проверьте переменные окружения
env | grep BOT

# 4. Проверьте зависимости
pip list
```

### База данных недоступна:

```bash
# Проверьте права доступа
ls -la data/

# Пересоздайте базу
python reset_database.py
```

### Бот работает, но не отвечает:

1. Проверьте CHAT_ID
2. Убедитесь, что бот админ в группе
3. Проверьте логи на ошибки

---

## 🔄 Обновление бота

### Git + systemd:

```bash
# 1. Перейдите в директорию
cd /path/to/she_codes_bot

# 2. Остановите бота
sudo systemctl stop chatquest-bot

# 3. Обновите код
git pull origin main

# 4. Обновите зависимости (если нужно)
venv/bin/pip install -r requirements.txt

# 5. Запустите бота
sudo systemctl start chatquest-bot

# 6. Проверьте статус
sudo systemctl status chatquest-bot
```

### Docker:

```bash
# 1. Остановите контейнер
docker-compose down

# 2. Обновите код
git pull origin main

# 3. Пересоберите образ
docker-compose build

# 4. Запустите
docker-compose up -d
```

---

## 📝 Рекомендации

### Для production:

1. ✅ Используйте systemd или Docker
2. ✅ Настройте автоматический перезапуск
3. ✅ Регулярно делайте бэкапы базы
4. ✅ Мониторьте логи
5. ✅ Используйте PostgreSQL вместо SQLite (опционально)

### Переход на PostgreSQL:

```bash
# 1. Установите PostgreSQL
sudo apt install postgresql postgresql-contrib

# 2. Установите psycopg2
pip install psycopg2-binary

# 3. В .env измените:
DATABASE_URL=postgresql://user:password@localhost/chatquest_bot

# 4. Адаптируйте database.py для PostgreSQL
```

---

## 🎉 Готово!

После деплоя:

1. Проверьте `/start` в группе
2. Отправьте `/send_task` (оператор)
3. Проверьте `/top`
4. Мониторьте логи

**Удачи с деплоем! 🚀**

---

*Если возникли проблемы, проверьте логи или создайте Issue на GitHub*