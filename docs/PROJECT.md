# AI-HR Project Overview

## Vision
AI-платформа для автоматизации HR-процессов: от скрининга кандидатов до онбординга.

## Current Phase
🔬 **Phase 1: Discovery** — исследование гипотез, определение MVP

## Quick Links
- [Гипотезы](./HYPOTHESES.md)
- [Архитектурные решения](./decisions/)
- [Roadmap](#roadmap)

---

## Roadmap

### Phase 1: Discovery 🔬
**Цель:** Валидировать ключевые гипотезы, определить MVP

| Milestone | Задачи | Критерий завершения |
|-----------|--------|---------------------|
| **1.1 Research** | Анализ конкурентов, интервью с HR | 5+ интервью проведено |
| **1.2 Hypothesis Validation** | Тест H1 (AI-скрининг), прототип промптов | Точность >80% на 10 резюме |
| **1.3 MVP Definition** | Scope, user stories, wireframes | Документ MVP утверждён |

**Deliverables:**
- [ ] Competitive analysis
- [ ] User interview notes
- [ ] Работающий промпт для скрининга резюме
- [ ] MVP scope document
- [ ] Lo-fi wireframes

---

### Phase 2: Foundation 🏗️
**Цель:** Базовая инфраструктура и core функционал

| Milestone | Задачи | Критерий завершения |
|-----------|--------|---------------------|
| **2.1 Backend Setup** | FastAPI, PostgreSQL, Docker | API healthcheck работает |
| **2.2 Auth & Users** | Регистрация, логин, роли | Можно залогиниться |
| **2.3 Resume Parser** | Upload PDF, извлечение данных | Парсинг 90%+ резюме |
| **2.4 AI Integration** | Claude API, промпты, rate limits | AI-скоринг работает |

**Deliverables:**
- [ ] Docker Compose setup
- [ ] User auth (email + password)
- [ ] Resume upload endpoint
- [ ] AI scoring endpoint
- [ ] Basic admin panel

---

### Phase 3: MVP Launch 🚀
**Цель:** Первые пользователи, сбор feedback

| Milestone | Задачи | Критерий завершения |
|-----------|--------|---------------------|
| **3.1 Core UI** | Next.js, candidate pipeline view | UI usable |
| **3.2 Candidate Pipeline** | Kanban, статусы, фильтры | Можно двигать кандидатов |
| **3.3 Job Postings** | CRUD вакансий, требования | Можно создать вакансию |
| **3.4 Beta Launch** | Deploy, onboard 3-5 users | 3+ активных пользователя |

**Deliverables:**
- [ ] Production deployment (Vercel + Railway/Render)
- [ ] Candidate kanban board
- [ ] Job posting management
- [ ] Email notifications
- [ ] User feedback система

---

### Phase 4: Growth 📈
**Цель:** Расширение функционала на основе feedback

| Milestone | Задачи | Критерий завершения |
|-----------|--------|---------------------|
| **4.1 Interview Scheduler** | Calendar integration, auto-slots | Интервью можно запланировать |
| **4.2 AI Enhancements** | Генерация вопросов, саммари | Используется в 50%+ интервью |
| **4.3 Analytics** | Dashboards, воронка найма | Видна конверсия по этапам |
| **4.4 Integrations** | Telegram бот, Slack, email parsing | 2+ интеграции работают |

**Deliverables:**
- [ ] Google Calendar / Outlook integration
- [ ] Interview question generator
- [ ] Hiring analytics dashboard
- [ ] Telegram bot для нотификаций

---

### Phase 5: Scale 🌍
**Цель:** Масштабирование и монетизация

| Milestone | Задачи | Критерий завершения |
|-----------|--------|---------------------|
| **5.1 Multi-tenancy** | Изоляция данных, billing | Несколько компаний на платформе |
| **5.2 Onboarding Module** | Чеклисты, документы, tasks | Онбординг автоматизирован |
| **5.3 Advanced AI** | Custom models, fine-tuning | Улучшение метрик на 20% |
| **5.4 Monetization** | Pricing, Stripe, subscriptions | Первая оплата получена |

**Deliverables:**
- [ ] SaaS billing (Stripe)
- [ ] Onboarding workflows
- [ ] White-label опция
- [ ] API для интеграций

---

## Key Metrics

| Metric | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|--------|---------|---------|---------|---------|
| Active users | 1 (dev) | 5 | 20 | 100+ |
| Resumes processed | 50 | 500 | 2000 | 10000+ |
| AI accuracy | 80% | 85% | 90% | 95% |
| Time to screen | <30s | <20s | <15s | <10s |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI accuracy insufficient | High | Итеративное улучшение промптов, fallback на ручной скрининг |
| Low adoption | High | Early user interviews, quick iteration |
| API costs | Medium | Caching, batching, usage limits |
| Data privacy (GDPR) | High | Data encryption, consent management |

---

## Team
- Product + Dev: @nik
- AI: Claude

## Tech Stack
- Backend: Python + FastAPI
- Database: PostgreSQL
- Frontend: Next.js
- AI: Claude API (Anthropic)
- Deploy: Docker, Vercel, Railway
