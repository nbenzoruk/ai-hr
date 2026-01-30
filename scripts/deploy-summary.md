# 🚀 Railway Deployment - Quick Summary

## ✅ Подготовка завершена!

Все необходимые файлы для деплоя созданы:

### Файлы конфигурации
- ✅ `railway.toml` - Railway конфигурация
- ✅ `.dockerignore` - Оптимизация Docker билдов
- ✅ `.env.railway.example` - Шаблон переменных окружения
- ✅ `docker-compose.railway.yml` - Production compose файл
- ✅ `DEPLOYMENT.md` - Полная инструкция по деплою
- ✅ `scripts/pre-deploy-check.sh` - Чеклист перед деплоем

---

## 🎯 Два способа деплоя

### Способ 1: Railway UI (самый простой)

1. Перейди на [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo**
3. Выбери репозиторий `ai-hr`
4. Railway автоматически обнаружит `docker-compose.yml`
5. **Добавь PostgreSQL:**
   - Нажми "+ New" → "Database" → "PostgreSQL"
6. **Настрой переменные для каждого сервиса:**

   **Backend:**
   ```
   OPENAI_API_KEY=sk-proj-ваш-ключ
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ENVIRONMENT=production
   ```

   **Frontend Candidate:**
   ```
   BACKEND_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
   DEMO_MODE=false
   ```

   **Frontend HR:**
   ```
   BACKEND_URL=${{backend.RAILWAY_PUBLIC_DOMAIN}}
   ```

7. **Включи Public Domains** для всех 3 сервисов
8. Дождись деплоя (5-10 минут)
9. Готово! 🎉

### Способ 2: Railway CLI

```bash
# Установка CLI
brew install railway
# или
npm i -g @railway/cli

# Авторизация
railway login

# Инициализация
cd /Users/nik/Documents/ai-projects-code/ai-hr
railway init

# Добавление PostgreSQL
railway add --database postgres

# Установка переменных
railway variables set OPENAI_API_KEY="sk-proj-ваш-ключ"

# Деплой
railway up

# Получение URL
railway domain
```

---

## 📝 Следующие шаги

### 1. Пуш в GitHub (если ещё не сделал)

```bash
cd /Users/nik/Documents/ai-projects-code/ai-hr
git add .
git commit -m "feat: add Railway deployment config"
git push origin main
```

### 2. Деплой на Railway

Следуй инструкциям в [DEPLOYMENT.md](../DEPLOYMENT.md)

### 3. Тестирование

После деплоя получишь 3 URL:
- `https://your-backend.up.railway.app`
- `https://your-candidate.up.railway.app`
- `https://your-hr.up.railway.app`

**Чеклист тестирования:**
- [ ] Backend `/docs` открывается
- [ ] Candidate Portal загружается
- [ ] HR Panel загружается
- [ ] Создал тестовую вакансию
- [ ] Прошёл воронку как кандидат
- [ ] Результаты видны в HR Panel

### 4. Отправка HR-у

Отправь только эти 2 ссылки:

```
🎯 Портал для кандидатов:
https://your-candidate.up.railway.app

👔 Панель для HR:
https://your-hr.up.railway.app
```

---

## 💰 Стоимость

- **Trial:** $5 бесплатно при регистрации (2-3 недели)
- **После:** ~$8-11/месяц
  - PostgreSQL: $5/мес
  - Backend: $1-2/мес
  - 2x Frontend: $2-4/мес

---

## 🔧 Полезные команды Railway

```bash
# Просмотр логов
railway logs
railway logs --service backend

# Просмотр переменных
railway variables

# Открыть Dashboard
railway open

# Статус деплоя
railway status

# Откатиться на предыдущую версию
railway rollback
```

---

## 📚 Дополнительная информация

- **Полная инструкция:** [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Railway Docs:** https://docs.railway.app
- **Railway Discord:** https://discord.gg/railway

---

**Готов к деплою? Вперёд! 🚀**
