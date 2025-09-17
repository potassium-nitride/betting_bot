# Подробная инструкция по развертыванию

Данная инструкция содержит пошаговые руководства по развертыванию Telegram Betting Bot на различных платформах.

## Подготовка к развертыванию

### 1. Получение Telegram Bot Token

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен в формате `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Получение Admin ID

1. Отправьте любое сообщение вашему боту
2. Откройте в браузере: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Найдите ваш `user_id` в ответе JSON
4. Сохраните этот ID для использования в качестве ADMIN_IDS

## Развертывание на Heroku

### Способ 1: Через Heroku CLI

#### Предварительные требования
- Установленный [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- Git репозиторий с кодом бота

#### Пошаговая инструкция

1. **Вход в Heroku**
```bash
heroku login
```

2. **Создание приложения**
```bash
heroku create your-betting-bot-name
```

3. **Добавление PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini -a your-betting-bot-name
```

4. **Настройка переменных окружения**
```bash
heroku config:set BOT_TOKEN="your_bot_token_here" -a your-betting-bot-name
heroku config:set ADMIN_IDS="your_admin_id_here" -a your-betting-bot-name
heroku config:set WEBHOOK_URL="https://your-betting-bot-name.herokuapp.com/webhook" -a your-betting-bot-name
```

5. **Развертывание**
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

6. **Проверка логов**
```bash
heroku logs --tail -a your-betting-bot-name
```

### Способ 2: Через Heroku Dashboard

1. Зайдите на [dashboard.heroku.com](https://dashboard.heroku.com)
2. Нажмите "New" → "Create new app"
3. Введите имя приложения и выберите регион
4. В разделе "Deployment method" выберите "GitHub"
5. Подключите ваш репозиторий
6. В разделе "Add-ons" добавьте "Heroku Postgres"
7. В разделе "Settings" → "Config Vars" добавьте переменные окружения
8. В разделе "Deploy" нажмите "Deploy Branch"

### Способ 3: Heroku Button

Добавьте в ваш README.md:

```markdown
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/your-username/betting-bot)
```

## Развертывание на Railway

### Через Railway Dashboard

1. **Регистрация и подключение GitHub**
   - Зайдите на [railway.app](https://railway.app)
   - Войдите через GitHub аккаунт

2. **Создание проекта**
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Выберите ваш репозиторий

3. **Добавление базы данных**
   - В проекте нажмите "New"
   - Выберите "Database" → "PostgreSQL"

4. **Настройка переменных окружения**
   - Перейдите в настройки сервиса
   - Добавьте переменные в разделе "Variables":
     ```
     BOT_TOKEN=your_bot_token_here
     ADMIN_IDS=your_admin_id_here
     DATABASE_URL=${{Postgres.DATABASE_URL}}
     ```

5. **Развертывание**
   - Railway автоматически развернет приложение
   - Проверьте логи в разделе "Deployments"

### Через Railway CLI

1. **Установка CLI**
```bash
npm install -g @railway/cli
```

2. **Вход в аккаунт**
```bash
railway login
```

3. **Инициализация проекта**
```bash
railway init
```

4. **Добавление PostgreSQL**
```bash
railway add postgresql
```

5. **Настройка переменных**
```bash
railway variables set BOT_TOKEN=your_bot_token_here
railway variables set ADMIN_IDS=your_admin_id_here
```

6. **Развертывание**
```bash
railway up
```

## Развертывание на Render

### Через Render Dashboard

1. **Создание аккаунта**
   - Зайдите на [render.com](https://render.com)
   - Зарегистрируйтесь через GitHub

2. **Создание Web Service**
   - Нажмите "New" → "Web Service"
   - Подключите GitHub репозиторий
   - Настройте параметры:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `python src/bot.py`

3. **Добавление PostgreSQL**
   - Создайте новый PostgreSQL сервис
   - Скопируйте Internal Database URL

4. **Настройка переменных окружения**
   - В настройках Web Service добавьте:
     ```
     BOT_TOKEN=your_bot_token_here
     ADMIN_IDS=your_admin_id_here
     DATABASE_URL=your_postgres_url_here
     ```

5. **Развертывание**
   - Render автоматически развернет приложение
   - Проверьте статус в Dashboard

## Развертывание на VPS

### Подготовка сервера (Ubuntu 20.04+)

1. **Обновление системы**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Установка Python и зависимостей**
```bash
sudo apt install python3 python3-pip python3-venv git postgresql postgresql-contrib nginx -y
```

3. **Создание пользователя для приложения**
```bash
sudo adduser betting_bot
sudo usermod -aG sudo betting_bot
```

4. **Настройка PostgreSQL**
```bash
sudo -u postgres createuser --interactive betting_bot
sudo -u postgres createdb betting_bot_db
sudo -u postgres psql -c "ALTER USER betting_bot PASSWORD 'your_password';"
```

### Развертывание приложения

1. **Переключение на пользователя приложения**
```bash
sudo su - betting_bot
```

2. **Клонирование репозитория**
```bash
git clone https://github.com/your-username/betting-bot.git
cd betting-bot
```

3. **Создание виртуального окружения**
```bash
python3 -m venv venv
source venv/bin/activate
```

4. **Установка зависимостей**
```bash
pip install -r requirements.txt
```

5. **Настройка переменных окружения**
```bash
cp .env.example .env
nano .env
```

Заполните файл .env:
```
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_admin_id_here
DATABASE_URL=postgresql://betting_bot:your_password@localhost/betting_bot_db
```

6. **Создание systemd сервиса**
```bash
sudo nano /etc/systemd/system/betting-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Telegram Betting Bot
After=network.target

[Service]
Type=simple
User=betting_bot
WorkingDirectory=/home/betting_bot/betting-bot
Environment=PATH=/home/betting_bot/betting-bot/venv/bin
ExecStart=/home/betting_bot/betting-bot/venv/bin/python src/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

7. **Запуск сервиса**
```bash
sudo systemctl daemon-reload
sudo systemctl enable betting-bot
sudo systemctl start betting-bot
```

8. **Проверка статуса**
```bash
sudo systemctl status betting-bot
```

## Развертывание с Docker

### Docker Compose (рекомендуется)

1. **Создание docker-compose.yml**
```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - DATABASE_URL=postgresql://postgres:password@db:5432/betting_bot
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=betting_bot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

2. **Создание .env файла**
```bash
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_admin_id_here
```

3. **Запуск**
```bash
docker-compose up -d
```

### Отдельные контейнеры

1. **Создание сети**
```bash
docker network create betting-bot-network
```

2. **Запуск PostgreSQL**
```bash
docker run -d \
  --name betting-bot-db \
  --network betting-bot-network \
  -e POSTGRES_DB=betting_bot \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -v betting_bot_data:/var/lib/postgresql/data \
  postgres:15
```

3. **Сборка и запуск бота**
```bash
docker build -t betting-bot .

docker run -d \
  --name betting-bot-app \
  --network betting-bot-network \
  -e BOT_TOKEN=your_bot_token_here \
  -e ADMIN_IDS=your_admin_id_here \
  -e DATABASE_URL=postgresql://postgres:password@betting-bot-db:5432/betting_bot \
  betting-bot
```

## Настройка мониторинга

### Логирование

1. **Настройка логов в systemd**
```bash
sudo journalctl -u betting-bot -f
```

2. **Настройка ротации логов**
```bash
sudo nano /etc/logrotate.d/betting-bot
```

Содержимое:
```
/var/log/betting-bot/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 betting_bot betting_bot
}
```

### Мониторинг с помощью Prometheus

1. **Добавление метрик в код**
```python
from prometheus_client import Counter, Histogram, start_http_server

# Метрики
BETS_TOTAL = Counter('bets_total', 'Total number of bets')
BET_AMOUNT = Histogram('bet_amount', 'Bet amounts')

# Запуск сервера метрик
start_http_server(8001)
```

2. **Настройка Prometheus**
```yaml
scrape_configs:
  - job_name: 'betting-bot'
    static_configs:
      - targets: ['localhost:8001']
```

## Резервное копирование

### Автоматическое резервное копирование PostgreSQL

1. **Создание скрипта резервного копирования**
```bash
#!/bin/bash
BACKUP_DIR="/home/betting_bot/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="betting_bot_db"

mkdir -p $BACKUP_DIR
pg_dump $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

2. **Добавление в crontab**
```bash
crontab -e
```

Добавить строку:
```
0 2 * * * /home/betting_bot/backup.sh
```

## Устранение неполадок

### Частые проблемы и решения

1. **Бот не отвечает**
   - Проверьте правильность BOT_TOKEN
   - Убедитесь, что сервис запущен: `systemctl status betting-bot`
   - Проверьте логи: `journalctl -u betting-bot -f`

2. **Ошибки базы данных**
   - Проверьте подключение к PostgreSQL
   - Убедитесь в правильности DATABASE_URL
   - Проверьте права доступа пользователя к базе

3. **Проблемы с памятью**
   - Увеличьте лимиты в systemd сервисе
   - Оптимизируйте запросы к базе данных
   - Рассмотрите использование connection pooling

4. **Высокая нагрузка**
   - Настройте rate limiting
   - Используйте кэширование для частых запросов
   - Рассмотрите горизонтальное масштабирование

### Полезные команды для диагностики

```bash
# Проверка статуса сервиса
sudo systemctl status betting-bot

# Просмотр логов
sudo journalctl -u betting-bot -f

# Проверка использования ресурсов
htop
df -h
free -h

# Проверка подключения к базе данных
psql -h localhost -U betting_bot -d betting_bot_db

# Проверка портов
netstat -tlnp | grep :8000
```

## Обновление приложения

### Обновление на VPS

1. **Остановка сервиса**
```bash
sudo systemctl stop betting-bot
```

2. **Обновление кода**
```bash
cd /home/betting_bot/betting-bot
git pull origin main
```

3. **Обновление зависимостей**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

4. **Запуск сервиса**
```bash
sudo systemctl start betting-bot
```

### Обновление в Docker

1. **Пересборка образа**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Обновление на Heroku

```bash
git push heroku main
```

## Масштабирование

### Горизонтальное масштабирование

1. **Использование Redis для состояния**
2. **Настройка load balancer**
3. **Разделение на микросервисы**
4. **Использование очередей сообщений**

### Вертикальное масштабирование

1. **Увеличение ресурсов сервера**
2. **Оптимизация базы данных**
3. **Настройка индексов**
4. **Использование connection pooling**

---

Эта инструкция покрывает основные сценарии развертывания. Для специфических случаев обратитесь к документации соответствующих платформ.
