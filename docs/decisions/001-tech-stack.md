# ADR-001: Выбор технологического стека

## Status
ACCEPTED

## Context
Нужно выбрать стек для AI-HR платформы. Ключевые требования:
- Быстрая интеграция с AI (Claude API)
- Скорость разработки MVP
- Масштабируемость при росте

## Decision
**Backend: Python + FastAPI**
- Отличная поддержка AI/ML библиотек
- Async из коробки
- Автогенерация OpenAPI документации

**Database: PostgreSQL**
- JSONB для гибких схем
- Надёжность и экосистема

**Frontend: Next.js (позже)**
- SSR для SEO
- React экосистема

**AI: Claude API (Anthropic)**
- Качественный анализ текста
- Хорошая документация

## Alternatives Considered

### Backend
1. **Node.js + Express**
   - ✅ Единый язык с фронтом
   - ❌ Менее удобная работа с AI библиотеками

2. **Go**
   - ✅ Производительность
   - ❌ Медленнее разработка, меньше AI-библиотек

### Database
1. **MongoDB**
   - ✅ Гибкая схема
   - ❌ Сложнее для связанных данных (кандидаты-вакансии)

## Consequences

### Positive
- Быстрый старт разработки
- Лёгкая интеграция с Claude API
- Понятная документация API из коробки

### Negative
- Два языка (Python backend + JS frontend)
- Нужен Python-разработчик

## References
- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Anthropic API](https://docs.anthropic.com/)
