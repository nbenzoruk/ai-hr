"""
SQLAlchemy models for AI-HR
"""
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from database import Base


class Job(Base):
    """Вакансия, созданная HR"""
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Исходный бриф
    job_title: Mapped[str] = mapped_column(String(255))
    company_name: Mapped[str] = mapped_column(String(255))
    company_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sales_segment: Mapped[str] = mapped_column(String(255))
    salary_range: Mapped[str] = mapped_column(String(255))
    sales_target: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    work_format: Mapped[str] = mapped_column(String(50), default="office")
    additional_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI-сгенерированные данные
    job_title_final: Mapped[str] = mapped_column(String(255))
    job_description: Mapped[str] = mapped_column(Text)
    requirements: Mapped[dict] = mapped_column(JSON, default=list)  # List[str]
    nice_to_have: Mapped[dict] = mapped_column(JSON, default=list)  # List[str]
    benefits: Mapped[dict] = mapped_column(JSON, default=list)  # List[str]
    screening_questions: Mapped[dict] = mapped_column(JSON, default=list)  # List[dict]
    salary_display: Mapped[str] = mapped_column(String(255))
    tags: Mapped[dict] = mapped_column(JSON, default=list)  # List[str]

    # Критерии скрининга
    screening_criteria: Mapped[dict] = mapped_column(JSON, default=dict)
    min_resume_score: Mapped[int] = mapped_column(Integer, default=65)

    # Метаданные
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    candidates: Mapped[List["Candidate"]] = relationship(back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    """Кандидат, проходящий отбор"""
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))

    # Базовая информация
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Статус прохождения
    status: Mapped[str] = mapped_column(String(50), default="in_progress")  # in_progress, completed, rejected
    current_stage: Mapped[str] = mapped_column(String(50), default="screening")
    rejection_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Результаты этапов (JSON для гибкости)
    screening_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    screening_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resume_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_red_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resume_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    motivation_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    primary_motivation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    secondary_motivation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    motivation_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cognitive_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cognitive_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cognitive_passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    interview_conversation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    interview_assessment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Stage 7: Личностный профиль
    personality_profile: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    personality_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    personality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Stage 8: Сейлз-блок
    sales_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sales_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sales_concerns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Общие красные флаги (сводка)
    red_flags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    job: Mapped["Job"] = relationship(back_populates="candidates")


class SystemSettings(Base):
    """Global system settings (singleton - only one row)"""
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    # AI Settings
    ai_temperature: Mapped[float] = mapped_column(Float, default=0.7)
    ai_model_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Default thresholds
    default_resume_threshold: Mapped[int] = mapped_column(Integer, default=65)
    default_cognitive_pass: Mapped[int] = mapped_column(Integer, default=2)  # out of 3
    default_personality_threshold: Mapped[int] = mapped_column(Integer, default=40)
    default_sales_threshold: Mapped[int] = mapped_column(Integer, default=40)

    # Screening defaults
    default_screening_criteria: Mapped[dict] = mapped_column(JSON, default=dict)

    # Metadata
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class Prompt(Base):
    """Configurable AI prompts"""
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identification
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Prompt content
    system_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_template: Mapped[str] = mapped_column(Text)

    # Variables (list of expected placeholders)
    template_variables: Mapped[dict] = mapped_column(JSON, default=list)

    # AI parameters override
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StageDefinition(Base):
    """Configurable recruitment stages"""
    __tablename__ = "stage_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Identification
    key: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    icon: Mapped[str] = mapped_column(String(10), default="📋")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stage behavior
    stage_type: Mapped[str] = mapped_column(String(50))  # form, ai_analysis, test, chat
    is_blocking: Mapped[bool] = mapped_column(Boolean, default=True)
    is_skippable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Ordering
    default_order: Mapped[int] = mapped_column(Integer, default=0)

    # Pass criteria
    pass_criteria: Mapped[dict] = mapped_column(JSON, default=dict)

    # Related prompt
    prompt_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
