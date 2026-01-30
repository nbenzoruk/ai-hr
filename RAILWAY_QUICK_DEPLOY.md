# 🚀 Railway - Быстрый деплой (5 минут!)

## Вариант 1: Railway CLI (САМЫЙ БЫСТРЫЙ)

### Установка CLI

```bash
# macOS
brew install railway

# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Linux
bash <(curl -fsSL https://railway.app/install.sh)
```

### Деплой одной командой

```bash
# 1. Авторизация
railway login

# 2. Создать проект (выбери team)
railway init

# 3. Добавить PostgreSQL
railway add --database postgres

# 4. Деплой ВСЕХ сервисов автоматом!
railway up --detach

# 5. Открыть Dashboard
railway open
```

**Готово!** Railway автоматически:
- ✅ Найдёт docker-compose.yml
- ✅ Создаст 3 сервиса (backend, frontend-candidate, frontend-hr)
- ✅ Подключит PostgreSQL
- ✅ Настроит сеть между сервисами
- ✅ Выдаст публичные URL

---

## Вариант 2: Railway UI Template (ЧЕРЕЗ БРАУЗЕР)

### Шаг 1: Создай проект из GitHub

1. Railway Dashboard → **New Project**
2. **Deploy from GitHub repo** → выбери `ai-hr`
3. Railway автоматически обнаружит docker-compose

### Шаг 2: Настрой переменные окружения

Railway создаст сервисы, но нужно добавить:

**Backend:**
```
AI_API_KEY=sk-or-v1-твой-ключ
AI_API_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL_NAME=google/gemini-2.0-flash-001
ENVIRONMENT=production
```

**Frontend Candidate & HR:**
```
BACKEND_URL=${{backend.RAILWAY_PRIVATE_DOMAIN}}
ENVIRONMENT=production
```

### Шаг 3: Добавь PostgreSQL

1. **+ New** → **Database** → **PostgreSQL**
2. Railway автоматически подключит `DATABASE_URL` к backend

---

## 🎯 Настройки для успешного деплоя

### Обновить docker-compose.yml

Убедись что в `docker-compose.yml` указаны правильные пути:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/backend.Dockerfile
    # ...

  frontend-candidate:
    build:
      context: .
      dockerfile: Dockerfile.candidate
    # ...

  frontend-hr:
    build:
      context: .
      dockerfile: Dockerfile.hr
    # ...
```

---

## ✅ Проверка после деплоя

```bash
# Через CLI
railway status

# Получить URL всех сервисов
railway service

# Открыть backend в браузере
railway open backend

# Логи
railway logs backend
railway logs frontend-candidate
```

---

## 🔧 Troubleshooting

### "Healthcheck failed"

```bash
# Проверь логи
railway logs backend --tail 100

# Redeploy
railway redeploy
```

### "Service not found"

Railway может не обнаружить docker-compose автоматически.

**Решение:**
```bash
# Явно указать docker-compose
railway up --service backend
railway up --service frontend-candidate
railway up --service frontend-hr
```

---

## 💡 Полезные команды

```bash
# Посмотреть все проекты
railway list

# Переключиться на проект
railway link

# Посмотреть переменные окружения
railway variables

# Добавить переменную
railway variables set KEY=value

# Удалить сервис
railway service delete frontend-candidate

# Откатиться на предыдущую версию
railway rollback
```

---

## 🎉 После успешного деплоя

Railway выдаст URL типа:
```
Backend: https://ai-hr-backend-production.up.railway.app
Candidate: https://ai-hr-candidate-production.up.railway.app
HR: https://ai-hr-hr-production.up.railway.app
```

**Обнови `ALLOWED_ORIGINS` в backend:**
```bash
railway variables set ALLOWED_ORIGINS="https://ai-hr-candidate-production.up.railway.app,https://ai-hr-hr-production.up.railway.app" --service backend
```

---

**Время деплоя: 5-10 минут вместо часов ручной настройки!** 🚀
