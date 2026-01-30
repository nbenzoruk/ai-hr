# 🚀 ДЕПЛОЙ ПРЯМО СЕЙЧАС - 5 минут!

## ✅ ВСЁ УЖЕ ГОТОВО:

1. ✅ Railway CLI установлен
2. ✅ Docker-compose обновлён
3. ✅ Все Dockerfiles готовы
4. ✅ Код в GitHub запушен

---

## 🎯 ОСТАЛОСЬ 5 КОМАНД:

Открой терминал и выполни:

```bash
# Перейди в проект
cd /Users/nik/Documents/ai-projects-code/ai-hr

# 1. Авторизация (откроется браузер)
railway login

# 2. Создать проект
railway init
# Выбери: Create new Project
# Имя: ai-hr

# 3. Добавить PostgreSQL
railway add

# Выбери: PostgreSQL
# Дождись создания (~10 секунд)

# 4. ДЕПЛОЙ ВСЕХ СЕРВИСОВ!
railway up

# Дождись завершения (~3-5 минут)

# 5. Добавить API ключ
railway variables set AI_API_KEY="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" --service backend
railway variables set AI_API_BASE_URL="https://openrouter.ai/api/v1" --service backend
railway variables set AI_MODEL_NAME="google/gemini-2.0-flash-001" --service backend
railway variables set ENVIRONMENT="production" --service backend

# 6. Обновить CORS для frontend
railway variables

# Скопируй URL frontend сервисов и добавь:
railway variables set ALLOWED_ORIGINS="https://frontend-candidate-url,https://frontend-hr-url" --service backend
```

---

## 📊 Что произойдёт:

Railway автоматически:
1. Прочитает `docker-compose.yml`
2. Создаст 3 сервиса:
   - **backend** (FastAPI)
   - **frontend-candidate** (Streamlit)
   - **frontend-hr** (Streamlit)
3. Подключит PostgreSQL
4. Выдаст публичные URL

---

## ✅ Проверка успеха:

```bash
# Посмотреть статус
railway status

# Получить URL всех сервисов
railway domain

# Открыть backend в браузере
railway open backend

# Или просто открыть Dashboard
railway open
```

---

## 🎉 После деплоя:

В Railway Dashboard увидишь:
```
✅ backend - Online
✅ frontend-candidate - Online
✅ frontend-hr - Online
✅ Postgres - Online
```

**URL будут типа:**
```
Backend: https://backend-production-xxx.up.railway.app
Candidate: https://frontend-candidate-production-xxx.up.railway.app
HR: https://frontend-hr-production-xxx.up.railway.app
```

---

## 🐛 Если что-то не так:

```bash
# Логи
railway logs backend --tail 100
railway logs frontend-candidate --tail 50

# Redeploy
railway redeploy --service backend

# Полный рестарт
railway restart
```

---

## 💡 Полезные команды:

```bash
# Список всех переменных
railway variables --service backend

# Удалить переменную
railway variables delete SOME_VAR --service backend

# Список всех сервисов
railway service

# Подключиться к базе данных
railway connect Postgres
```

---

**Время выполнения: 5-10 минут от начала до конца!** 🚀

**Удачи!** Если что-то пойдёт не так - скинь логи.
