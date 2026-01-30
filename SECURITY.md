# 🔒 Security Guidelines для AI-HR

## ✅ Что уже реализовано

### 1. **Защита секретов**
- ✅ API ключи в environment variables (не в коде)
- ✅ `.gitignore` настроен (`.env` файлы не коммитятся)
- ✅ `.env.example` для документации

### 2. **CORS Protection**
- ✅ CORSMiddleware настроен
- ✅ В production разрешены только specific origins
- ✅ Credentials разрешены для аутентификации

### 3. **SQL Injection Protection**
- ✅ SQLAlchemy ORM (параметризованные запросы)
- ✅ Pydantic валидация входных данных
- ✅ SQL echo отключен в production

### 4. **Database Security**
- ✅ Async PostgreSQL подключение
- ✅ Connection pooling
- ✅ DATABASE_URL из environment variables

### 5. **HTTPS/TLS**
- ✅ Railway автоматически предоставляет SSL сертификаты
- ✅ Все публичные домены используют HTTPS

---

## ⚠️ Рекомендации для production

### 1. **Rate Limiting** (TODO)

Добавить slowapi для защиты от DDoS:

\`\`\`python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/screen/stage2_screening")
@limiter.limit("10/minute")  # Максимум 10 запросов в минуту
async def screening_endpoint(...):
    ...
\`\`\`

**Критичные эндпоинты для rate limiting:**
- `/v1/jobs/generate` - 5/hour (генерация вакансий)
- `/v1/screen/*` - 10/minute (AI скрининг)
- `/v1/candidates` - 20/minute (создание кандидатов)

---

### 2. **CORS Origins**

**Перед деплоем обнови ALLOWED_ORIGINS:**

В Railway Variables добавь:
\`\`\`
ALLOWED_ORIGINS=https://твой-frontend-candidate.up.railway.app,https://твой-frontend-hr.up.railway.app
\`\`\`

**Никогда не используй `*` в production!**

---

### 3. **Error Handling**

В production не показывай stack traces пользователям:

\`\`\`python
if ENVIRONMENT == "production":
    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
\`\`\`

---

### 4. **Audit Logging**

Добавь логирование важных событий:
- Создание/удаление вакансий
- Доступ к данным кандидатов
- Failed authentication attempts
- Rate limit violations

---

### 5. **API Key Rotation**

**OpenRouter API Key:**
- Меняй ключ каждые 90 дней
- Используй separate ключи для dev/prod
- Мониторь usage в OpenRouter Dashboard

**Railway:**
- Регулярно проверяй access logs
- Используй 2FA для Railway аккаунта

---

### 6. **Data Privacy**

**Персональные данные кандидатов:**
- ✅ Не логируй PII (имена, email, телефоны)
- ⚠️ TODO: Добавь GDPR compliant data retention policy
- ⚠️ TODO: Реализуй "Удалить мои данные" endpoint

**Соответствие GDPR:**
- Храни данные максимум 6 месяцев
- Предоставляй экспорт данных по запросу
- Удаляй данные при отказе кандидата

---

### 7. **OpenAI API Security**

**Best Practices:**
- ✅ Не отправляй PII в prompts (где возможно)
- ⚠️ TODO: Санитизируй входные данные перед отправкой в AI
- ⚠️ TODO: Добавь content filtering для AI ответов

**Защита от prompt injection:**
\`\`\`python
def sanitize_user_input(text: str) -> str:
    # Удали потенциально опасные инструкции
    dangerous_patterns = [
        "ignore previous instructions",
        "system:",
        "assistant:",
    ]
    for pattern in dangerous_patterns:
        text = text.replace(pattern, "")
    return text
\`\`\`

---

### 8. **Database Backups**

**Railway PostgreSQL:**
- ✅ Railway автоматически делает backups
- ⚠️ Настрой manual backup schedule (Settings → Backups)
- ⚠️ Тестируй restore process раз в месяц

---

### 9. **Environment Variables**

**Обязательные в production:**
\`\`\`bash
ENVIRONMENT=production
AI_API_KEY=sk-or-v1-...
AI_API_BASE_URL=https://openrouter.ai/api/v1
AI_MODEL_NAME=google/gemini-2.0-flash-001
DATABASE_URL=${{Postgres.DATABASE_URL}}
ALLOWED_ORIGINS=https://candidate.up.railway.app,https://hr.up.railway.app
\`\`\`

**Опциональные:**
\`\`\`bash
LOG_LEVEL=INFO
MAX_DB_CONNECTIONS=20
RATE_LIMIT_ENABLED=true
\`\`\`

---

### 10. **Monitoring & Alerts**

**Railway Dashboard:**
- Проверяй CPU/Memory usage
- Настрой alerts для downtime
- Мониторь API error rate

**OpenRouter Dashboard:**
- Проверяй API usage
- Настрой spending limits
- Мониторь latency

---

## 🚨 Incident Response Plan

### Если обнаружена утечка API ключа:

1. **Немедленно:**
   - Отзови ключ в OpenRouter Dashboard
   - Создай новый ключ
   - Обнови переменную в Railway
   - Redeploy сервисы

2. **В течение 24 часов:**
   - Проверь логи на подозрительную активность
   - Смени все пароли
   - Notify пользователей если их данные затронуты

3. **После инцидента:**
   - Документируй что произошло
   - Обнови security procedures
   - Проведи security review

---

## 📋 Security Checklist перед production

- [ ] CORS настроен с specific origins
- [ ] Rate limiting добавлен на критичные endpoints
- [ ] SQL echo отключен (ENVIRONMENT=production)
- [ ] Error handling не показывает stack traces
- [ ] API ключи ротируются раз в 90 дней
- [ ] Backups настроены и протестированы
- [ ] Monitoring и alerts настроены
- [ ] GDPR compliance проверен
- [ ] Prompt injection защита добавлена
- [ ] Audit logging реализован

---

## 🔗 Полезные ссылки

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Railway Security](https://docs.railway.app/reference/private-networking)
- [OpenRouter Best Practices](https://openrouter.ai/docs)

---

**Последнее обновление:** 2026-01-30
**Автор:** AI-HR Security Team
