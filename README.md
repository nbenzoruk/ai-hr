# AI-HR

🤖 **AI-powered рекрутинговая воронка** для автоматизации отбора кандидатов

## 🌐 Production (Live Demo)

| Сервис | URL |
|--------|-----|
| **Candidate Portal** | https://frontend-candidate-production.up.railway.app |
| **HR Panel** | https://frontend-hr-production.up.railway.app |
| **Backend API** | https://ai-hrnew-production.up.railway.app |

## 🚀 Быстрый старт

### Локальный запуск (Docker)

```bash
# Клонировать репозиторий
git clone https://github.com/nbenzoruk/ai-hr.git
cd ai-hr

# Настроить .env файл
cp src/backend/.env.example src/backend/.env
# Добавить OPENAI_API_KEY в .env

# Запустить все сервисы
docker-compose up -d

# Открыть в браузере
open http://localhost:8501  # Candidate Portal
open http://localhost:8502  # HR Panel
open http://localhost:8000/docs  # API Docs
```

### Деплой на Railway

Полная инструкция: [DEPLOYMENT.md](DEPLOYMENT.md)

Быстрый старт:
1. Зарегистрируйся на [railway.app](https://railway.app)
2. Deploy from GitHub → выбери этот репозиторий
3. Добавь PostgreSQL базу
4. Настрой переменные окружения (OPENAI_API_KEY)
5. Готово! 🎉

## 📋 Возможности

- ✅ **14 этапов воронки отбора** (скрининг, тесты, интервью)
- ✅ **AI-скоринг резюме** через OpenAI GPT
- ✅ **Когнитивные тесты** и оценка личности
- ✅ **Behavioral chat** с AI-интервьюером
- ✅ **Геймификация** (бейджи, прогресс-бар, XP)
- ✅ **HR Dashboard** для управления кандидатами
- ✅ **Генерация вакансий** через AI
- ✅ **PDF отчёты** по кандидатам

## 🛠 Технологии

- **Backend**: FastAPI, Python 3.11, SQLAlchemy
- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **AI**: OpenAI GPT-4
- **Deploy**: Docker, Railway

## 📖 Документация

- [Deployment Guide](DEPLOYMENT.md) - Деплой на Railway
- [API Docs](http://localhost:8000/docs) - Swagger документация
- [TODO](docs/TODO.md) - Планы развития
- [Marketing Audit](docs/marketing_audit_candidate_portal.md) - UX рекомендации

## 🤝 Контакты

**Автор:** Nikita Benzoruk
**GitHub:** [@nbenzoruk](https://github.com/nbenzoruk)
