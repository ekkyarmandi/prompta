from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    directory = Column(String(500), nullable=True)  # Project directory path
    tags = Column(JSON, default=list)  # List of project tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="projects")
    prompts = relationship("Prompt", back_populates="project", cascade="all, delete-orphan")

    # Composite index for user + name uniqueness
    __table_args__ = (
        Index("ix_user_project_name", "user_id", "name"),
        Index("ix_projects_directory", "directory"),
        Index("ix_projects_updated", "updated_at"),
    )

    def __repr__(self):
        return f"<Project(name='{self.name}', user_id='{self.user_id}')>"


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)  # Optional project association
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=False)  # File path
    tags = Column(JSON, default=list)  # List of tags
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_version_id = Column(
        String(36), ForeignKey("prompt_versions.id"), nullable=True
    )

    # Relationships
    user = relationship("User", back_populates="prompts")
    project = relationship("Project", back_populates="prompts")
    versions = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        foreign_keys="PromptVersion.prompt_id",
    )
    current_version = relationship(
        "PromptVersion", foreign_keys=[current_version_id], post_update=True
    )

    # Composite index for user + name uniqueness
    __table_args__ = (
        Index("ix_user_prompt_name", "user_id", "name"),
        Index("ix_prompts_location", "location"),
        Index("ix_prompts_updated", "updated_at"),
        Index("ix_prompts_project", "project_id"),
    )

    def __repr__(self):
        return f"<Prompt(name='{self.name}', user_id='{self.user_id}')>"


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_id = Column(String(36), ForeignKey("prompts.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    commit_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_current = Column(Boolean, default=False)

    # Relationships
    prompt = relationship("Prompt", back_populates="versions", foreign_keys=[prompt_id])

    # Composite index for prompt + version uniqueness
    __table_args__ = (
        Index("ix_prompt_version", "prompt_id", "version_number"),
        Index("ix_version_current", "is_current"),
    )

    def __repr__(self):
        return f"<PromptVersion(prompt_id='{self.prompt_id}', version={self.version_number})>"
