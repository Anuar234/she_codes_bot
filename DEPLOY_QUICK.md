# 🚀 Быстрый деплой - Шпаргалка

## ⚡ Самые простые способы (без сервера)

### 1. Railway.app (Рекомендуется!) ⭐

```bash
1. Зайди на railway.app
2. New Project → Deploy from GitHub
3. Выбери репозиторий
4. Добавь переменные:
   BOT_TOKEN=твой_токен
   CHAT_ID=id_чата
   OPERATOR_IDS=твой_id
5. Всё! Railway запустит бота автоматически
```

**Плюсы:** Бесплатно 500 часов/месяц, автодеплой, простота
**Время:** 3 минуты

---

### 2. Render.com

```bash
1. render.com → New → Web Service
2. Подключи GitHub
3. Start Command: python main.py
4. Добавь Environment Variables
5. Create Service
```

**Плюсы:** Бесплатный план, автодеплой
**Время:** 5 минут

---

### 3. Heroku

```bash
heroku login
heroku create your-bot
heroku config:set BOT_TOKEN=xxx CHAT_ID=xxx OPERATOR_IDS=xxx
git push heroku main
heroku ps:scale web=1
```

**Плюсы:** Надежно, много документации
**Минусы:** Платный после 550 часов
**Время:** 5 минут

---

## 🖥️ На своём сервере (VPS)

### Один скрипт установки:

```bash
# Скопируй и выполни на сервере:

sudo apt update && sudo apt install -y python3.11 python3-pip git
git clone https://github.com/your-repo/she_codes_bot.git
cd she_codes_bot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Отредактируй .env:
nano .env
# Вставь BOT_TOKEN, CHAT_ID, OPERATOR_IDS

# Запусти:
python main.py
```

---

### Как сервис (автозапуск):

```bash
# 1. Создай файл
sudo nano /etc/systemd/system/bot.service

# 2. Вставь (измени пути!):
[Unit]
Description=ChatQuest Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/she_codes_bot
ExecStart=/home/your-user/she_codes_bot/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target

# 3. Запусти:
sudo systemctl daemon-reload
sudo systemctl start bot
sudo systemctl enable bot
sudo systemctl status bot
```

---

## 🐳 Docker (самый быстрый)

```bash
# 1. Запусти одной командой:
docker-compose up -d

# 2. Проверь:
docker-compose logs -f

# 3. Всё работает!
```

---

## 📋 Что нужно перед деплоем

```
✅ BOT_TOKEN (от @BotFather)
✅ CHAT_ID (от @userinfobot в группе)
✅ OPERATOR_IDS (твой ID от @userinfobot)
```

---

## 🔧 После деплоя

```bash
# Проверь что бот работает:
1. /start в группе
2. /send_task (оператор)
3. /top

# Если не работает - смотри логи:
docker logs chatquest_bot              # Docker
sudo journalctl -u bot -f             # Systemd
heroku logs --tail                    # Heroku
```

---

## 💰 Бесплатные варианты

| Платформа | Лимит | Рекомендация |
|-----------|-------|--------------|
| Railway | 500 ч/мес | ⭐⭐⭐⭐⭐ |
| Render | Unlimited | ⭐⭐⭐⭐ |
| Fly.io | 3 VM | ⭐⭐⭐⭐ |
| Heroku | 550 ч/мес | ⭐⭐⭐ |

---

## 🆘 Проблемы?

```bash
# Бот не запускается:
python test_config.py

# Проверь переменные:
cat .env

# Проверь логи:
tail -f bot.log
```

---

## 🎯 Моя рекомендация

**Для новичков:** Railway.app
- Просто подключаешь GitHub
- Добавляешь 3 переменные
- Бот работает!

**Для опытных:** VPS + systemd
- Полный контроль
- Можно настроить всё как угодно
- Дешевле в долгосрочной перспективе

**Для тестов:** Docker локально
- docker-compose up -d
- Работает сразу

---

## ⚡ Самый быстрый способ

```bash
# 1. Запуши код на GitHub
git add .
git commit -m "Initial commit"
git push

# 2. railway.app → Deploy from GitHub

# 3. Добавь переменные в Railway

# 4. ГОТОВО! 🎉
```

---

**Полная документация:** [DEPLOY.md](DEPLOY.md)

**Нужна помощь?** Читай логи и [README.md](README.md)