# 🚀 Deployment на Railway - Пошаговая инструкция

## Обзор

Этот гайд поможет задеплоить AI-HR на Railway за ~15 минут.

**Что получим:**
- ✅ Backend API с публичным URL
- ✅ Candidate Portal (для кандидатов)
- ✅ HR Panel (для HR)
- ✅ PostgreSQL база данных
- ✅ HTTPS из коробки
- ✅ Auto-deploy из GitHub

**Стоимость:** ~$5-10/месяц ($5 trial credit при регистрации)

---

## 📋 Пререквизиты

1. **GitHub аккаунт** (для Railway авторизации)
2. **OpenAI API Key** ([platform.openai.com](https://platform.openai.com/api-keys))
3. **Railway аккаунт** (регистрация через GitHub)

---

## 🎯 Метод 1: Деплой через Railway UI (Рекомендуется)

### Шаг 1: Создание проекта на Railway

1. Перейди на [railway.app](https://railway.app)
2. Нажми **"Start a New Project"**
3. Выбери **"Deploy from GitHub repo"**
4. Авторизуй Railway в GitHub
5. Выбери репозиторий `ai-hr`

### Шаг 2: Добавление PostgreSQL

1. В проекте нажми **"+ New"**
2. Выбери **"Database"** → **"Add PostgreSQL"**
3. Railway автоматически создаст базу и переменную `DATABASE_URL`

### Шаг 3: Настройка Backend сервиса

1. Railway автоматически обнаружит `docker-compose.yml`
2. Создаст 3 сервиса: `backend`, `frontend-candidate`, `frontend-hr`
3. Для **backend** сервиса:
   - Перейди в **Variables**
   - Добавь переменные:
     ```
     OPENAI_API_KEY=sk-proj-ваш-ключ
     DATABASE_URL=${{Postgres.DATABASE_URL}}
     ENVIRONMENT=production
     ```
   - Включи **Public Domain** (Settings → Networking → Generate Domain)
   - Запиши URL: `https://ai-hr-backend-production.up.railway.app`

### Шаг 4: Настройка Frontend Candidate

1. Перейди в сервис **frontend-candidate**
2. Settings → Build:
   - **Dockerfile Path:** `docker/frontend.Dockerfile`
   - **Build Args:** `APP_FILE=app_candidate.py`
3. Variables:
   ```
   BACKEND_URL=https://ai-hr-backend-production.up.railway.app
   DEMO_MODE=false
   ```
4. Включи **Public Domain**
5. Запиши URL: `https://ai-hr-candidate-production.up.railway.app`

### Шаг 5: Настройка Frontend HR

1. Перейди в сервис **frontend-hr**
2. Settings → Build:
   - **Dockerfile Path:** `docker/frontend.Dockerfile`
   - **Build Args:** `APP_FILE=app_hr.py`
3. Variables:
   ```
   BACKEND_URL=https://ai-hr-backend-production.up.railway.app
   ```
4. Включи **Public Domain**
5. Запиши URL: `https://ai-hr-hr-production.up.railway.app`

### Шаг 6: Деплой!

1. Railway автоматически начнёт билд всех сервисов
2. Дождись зелёных галочек (✓) на всех сервисах (~5-10 минут)
3. Проверь логи если что-то пошло не так

### Шаг 7: Проверка работы

Открой в браузере:
- **Backend API Docs:** `https://ai-hr-backend-production.up.railway.app/docs`
- **Candidate Portal:** `https://ai-hr-candidate-production.up.railway.app`
- **HR Panel:** `https://ai-hr-hr-production.up.railway.app`

---

## 🎯 Метод 2: Деплой через Railway CLI

### Установка Railway CLI

```bash
# macOS / Linux
brew install railway

# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# npm (кроссплатформенно)
npm i -g @railway/cli
```

### Деплой

```bash
# 1. Авторизация
railway login

# 2. Инициализация проекта
cd /Users/nik/Documents/ai-projects-code/ai-hr
railway init

# 3. Добавление PostgreSQL
railway add --database postgres

# 4. Установка переменных окружения
railway variables set OPENAI_API_KEY="sk-proj-ваш-ключ"
railway variables set ENVIRONMENT="production"

# 5. Деплой
railway up

# 6. Получение URL
railway domain
```

---

## 🔧 Настройка переменных окружения

### Backend сервис
```bash
OPENAI_API_KEY=sk-proj-ваш-ключ-от-openai
DATABASE_URL=${{Postgres.DATABASE_URL}}
ENVIRONMENT=production
```

### Frontend Candidate
```bash
BACKEND_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
DEMO_MODE=false
```

### Frontend HR
```bash
BACKEND_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
```

---

## 📊 Мониторинг и логи

### Просмотр логов в Railway UI
1. Открой проект на railway.app
2. Выбери сервис → вкладка **Logs**
3. Фильтруй по времени/уровню

### Логи через CLI
```bash
# Все сервисы
railway logs

# Конкретный сервис
railway logs --service backend
railway logs --service frontend-candidate
```

### Метрики
- CPU/Memory usage видны в Railway Dashboard
- Каждый сервис имеет отдельный график

---

## 🔄 Обновление (Continuous Deployment)

Railway автоматически деплоит при пуше в GitHub:

```bash
# Локально вносишь изменения
git add .
git commit -m "fix: улучшил UX"
git push origin main

# Railway автоматически:
# 1. Обнаружит изменения в GitHub
# 2. Запустит билд
# 3. Задеплоит новую версию
# 4. Переключит трафик на новую версию (zero-downtime)
```

### Отключить auto-deploy
Settings → Service Settings → **Disable Auto Deploy**

---

## 💰 Стоимость

### Бесплатный trial
- $5 credit при регистрации
- ~2-3 недели бесплатного использования

### После trial (~$5-10/мес)
| Ресурс | Стоимость |
|--------|-----------|
| PostgreSQL (512MB) | $5/мес |
| Backend (1 instance) | $1-2/мес |
| Frontend Candidate | $1-2/мес |
| Frontend HR | $1-2/мес |
| **ИТОГО** | **$8-11/мес** |

### Оптимизация стоимости
1. **Выключай неиспользуемые сервисы** (например, HR Panel ночью)
2. **Downgrade PostgreSQL** до 256MB если мало данных
3. **Используй Sleep Mode** для dev окружения

---

## 🐛 Troubleshooting

### Backend не запускается
```bash
# Проверь логи
railway logs --service backend

# Частые причины:
# 1. Нет OPENAI_API_KEY
# 2. Неправильный DATABASE_URL
# 3. Порт не 8000 (Railway ожидает 8000)
```

### Frontend не видит Backend
```bash
# Проверь BACKEND_URL в переменных frontend
# Должен быть: https://ai-hr-backend-production.up.railway.app
# НЕ: http://backend:8000 (это для docker-compose локально)
```

### База данных пустая
```bash
# Railway не запускает миграции автоматически
# Backend при старте сам создаёт таблицы (models.py)
# Если нужны начальные данные - добавь seed скрипт
```

### 502 Bad Gateway
- Backend ещё стартует (подожди 30-60 сек)
- Проверь healthcheck в логах
- Проверь что backend слушает `0.0.0.0:8000`

---

## 📝 Чеклист перед отправкой HR-у

- [ ] Все 3 сервиса развёрнуты (✓ зелёные галочки)
- [ ] Backend API `/docs` открывается
- [ ] Candidate Portal загружается
- [ ] HR Panel загружается
- [ ] Создал тестовую вакансию в HR Panel
- [ ] Прошёл воронку как кандидат
- [ ] Проверил что результаты видны в HR Panel
- [ ] Записал все URL в удобное место
- [ ] Проверил что OpenAI API работает (есть баланс)

---

## 🎉 Готовые ссылки для отправки HR-у

```
🎯 Портал для кандидатов:
https://ai-hr-candidate-production.up.railway.app

👔 Панель для HR:
https://ai-hr-hr-production.up.railway.app

📚 API документация (опционально):
https://ai-hr-backend-production.up.railway.app/docs
```

**Инструкция для HR:**
1. Открой HR Panel
2. Создай вакансию в разделе "Создать вакансию"
3. Скопируй ссылку на вакансию
4. Отправь кандидату (он пройдёт воронку)
5. Смотри результаты в разделе "Кандидаты"

---

## 📞 Поддержка

**Railway Docs:** https://docs.railway.app
**Railway Discord:** https://discord.gg/railway
**Railway Status:** https://status.railway.app

---

**Удачи с деплоем! 🚀**
