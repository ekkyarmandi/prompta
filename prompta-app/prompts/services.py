from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
import difflib
import math

from .models import Prompt, PromptVersion, Project
from .schemas import (
    PromptCreate, 
    PromptUpdate, 
    PromptVersionCreate, 
    PromptSearchParams,
    PromptDownloadParams,
    ProjectCreate,
    ProjectUpdate,
)
from auth.models import User


class ProjectService:
    """Service class for project-related operations"""

    @staticmethod
    def create_project(db: Session, user: User, project_data: ProjectCreate) -> Project:
        """Create a new project"""
        # Check if project with same name already exists for user
        existing_project = (
            db.query(Project)
            .filter(and_(Project.user_id == user.id, Project.name == project_data.name))
            .first()
        )

        if existing_project:
            raise ValueError(f"Project with name '{project_data.name}' already exists")

        # Create the project
        db_project = Project(
            user_id=user.id,
            name=project_data.name,
            description=project_data.description,
            directory=project_data.directory,
            tags=project_data.tags,
        )

        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        return db_project

    @staticmethod
    def get_project_by_id(db: Session, user: User, project_id: str) -> Optional[Project]:
        """Get a project by ID for a specific user"""
        return (
            db.query(Project)
            .filter(and_(Project.id == project_id, Project.user_id == user.id))
            .first()
        )

    @staticmethod
    def get_project_by_name(db: Session, user: User, name: str) -> Optional[Project]:
        """Get a project by name for a specific user"""
        return (
            db.query(Project)
            .filter(and_(Project.user_id == user.id, Project.name == name))
            .first()
        )

    @staticmethod
    def list_projects(
        db: Session, 
        user: User, 
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        directory: Optional[str] = None,
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Project], int]:
        """List projects with search and pagination"""
        db_query = db.query(Project).filter(
            and_(Project.user_id == user.id, Project.is_active == True)
        )

        # Apply search filters
        if query:
            search_term = f"%{query}%"
            db_query = db_query.filter(
                or_(
                    Project.name.ilike(search_term),
                    Project.description.ilike(search_term),
                )
            )

        if tags:
            from sqlalchemy import text
            for tag in tags:
                db_query = db_query.filter(
                    text(f"json_extract(tags, '$') LIKE '%\"{tag}\"%'")
                )

        if directory:
            directory_term = f"%{directory}%"
            db_query = db_query.filter(Project.directory.ilike(directory_term))

        # Get total count
        total = db_query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        projects = (
            db_query.order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return projects, total

    @staticmethod
    def update_project(
        db: Session, user: User, project_id: str, project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Update a project's metadata"""
        project = ProjectService.get_project_by_id(db, user, project_id)
        if not project:
            return None

        # Check if name is being changed and if it conflicts
        if project_data.name and project_data.name != project.name:
            existing_project = (
                db.query(Project)
                .filter(
                    and_(
                        Project.user_id == user.id,
                        Project.name == project_data.name,
                        Project.id != project_id,
                    )
                )
                .first()
            )

            if existing_project:
                raise ValueError(
                    f"Project with name '{project_data.name}' already exists"
                )

        # Update fields
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.directory is not None:
            project.directory = project_data.directory
        if project_data.tags is not None:
            project.tags = project_data.tags
        if project_data.is_active is not None:
            project.is_active = project_data.is_active

        db.commit()
        db.refresh(project)

        return project

    @staticmethod
    def delete_project(db: Session, user: User, project_id: str) -> bool:
        """Delete a project and all its prompts"""
        project = ProjectService.get_project_by_id(db, user, project_id)
        if not project:
            return False

        db.delete(project)
        db.commit()

        return True


class PromptService:
    """Service class for prompt-related operations"""

    @staticmethod
    def create_prompt(db: Session, user: User, prompt_data: PromptCreate) -> Prompt:
        """Create a new prompt with initial version"""
        # Check if prompt with same name already exists for user
        existing_prompt = (
            db.query(Prompt)
            .filter(and_(Prompt.user_id == user.id, Prompt.name == prompt_data.name))
            .first()
        )

        if existing_prompt:
            raise ValueError(f"Prompt with name '{prompt_data.name}' already exists")

        # Validate project_id if provided
        if prompt_data.project_id:
            project = ProjectService.get_project_by_id(db, user, prompt_data.project_id)
            if not project:
                raise ValueError(f"Project with ID '{prompt_data.project_id}' not found")

        # Create the prompt
        db_prompt = Prompt(
            user_id=user.id,
            project_id=prompt_data.project_id,
            name=prompt_data.name,
            description=prompt_data.description,
            location=prompt_data.location,
            tags=prompt_data.tags,
        )

        db.add(db_prompt)
        db.flush()  # Get the prompt ID

        # Create the initial version
        initial_version = PromptVersion(
            prompt_id=db_prompt.id,
            version_number=1,
            content=prompt_data.content,
            commit_message=prompt_data.commit_message or "Initial version",
            is_current=True,
        )

        db.add(initial_version)
        db.flush()  # Get the version ID

        # Set the current version
        db_prompt.current_version_id = initial_version.id

        db.commit()
        db.refresh(db_prompt)

        return db_prompt

    @staticmethod
    def get_prompt_by_id(db: Session, user: User, prompt_id: str) -> Optional[Prompt]:
        """Get a prompt by ID for a specific user"""
        return (
            db.query(Prompt)
            .options(joinedload(Prompt.project), joinedload(Prompt.current_version))
            .filter(and_(Prompt.id == prompt_id, Prompt.user_id == user.id))
            .first()
        )

    @staticmethod
    def get_prompt_by_name(db: Session, user: User, name: str) -> Optional[Prompt]:
        """Get a prompt by name for a specific user"""
        return (
            db.query(Prompt)
            .options(joinedload(Prompt.project), joinedload(Prompt.current_version))
            .filter(and_(Prompt.user_id == user.id, Prompt.name == name))
            .first()
        )

    @staticmethod
    def get_prompt_by_location(
        db: Session, user: User, location: str
    ) -> Optional[Prompt]:
        """Get a prompt by location for a specific user"""
        return (
            db.query(Prompt)
            .options(joinedload(Prompt.project), joinedload(Prompt.current_version))
            .filter(and_(Prompt.user_id == user.id, Prompt.location == location))
            .first()
        )

    @staticmethod
    def list_prompts(
        db: Session, user: User, search_params: PromptSearchParams
    ) -> Tuple[List[Prompt], int]:
        """List prompts with search and pagination"""
        query = (
            db.query(Prompt)
            .options(joinedload(Prompt.project), joinedload(Prompt.current_version))
            .filter(Prompt.user_id == user.id)
        )

        # Apply search filters
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    Prompt.name.ilike(search_term),
                    Prompt.description.ilike(search_term),
                    Prompt.location.ilike(search_term),
                )
            )

        if search_params.tags:
            # Filter by tags - use JSON_EXTRACT for SQLite compatibility
            from sqlalchemy import text

            for tag in search_params.tags:
                # Use LIKE with JSON string representation for SQLite compatibility
                query = query.filter(
                    text(f"json_extract(tags, '$') LIKE '%\"{tag}\"%'")
                )

        if search_params.location:
            location_term = f"%{search_params.location}%"
            query = query.filter(Prompt.location.ilike(location_term))

        if search_params.project_id:
            query = query.filter(Prompt.project_id == search_params.project_id)

        if search_params.project_name:
            query = query.join(Project).filter(Project.name == search_params.project_name)

        if search_params.directory:
            # Filter by project directory or prompt location containing directory
            directory_term = f"%{search_params.directory}%"
            query = query.outerjoin(Project).filter(
                or_(
                    Project.directory.ilike(directory_term),
                    Prompt.location.ilike(directory_term),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (search_params.page - 1) * search_params.page_size
        prompts = (
            query.order_by(Prompt.updated_at.desc())
            .offset(offset)
            .limit(search_params.page_size)
            .all()
        )

        return prompts, total

    @staticmethod
    def update_prompt(
        db: Session, user: User, prompt_id: str, prompt_data: PromptUpdate
    ) -> Optional[Prompt]:
        """Update a prompt's metadata"""
        prompt = PromptService.get_prompt_by_id(db, user, prompt_id)
        if not prompt:
            return None

        # Check if name is being changed and if it conflicts
        if prompt_data.name and prompt_data.name != prompt.name:
            existing_prompt = (
                db.query(Prompt)
                .filter(
                    and_(
                        Prompt.user_id == user.id,
                        Prompt.name == prompt_data.name,
                        Prompt.id != prompt_id,
                    )
                )
                .first()
            )

            if existing_prompt:
                raise ValueError(
                    f"Prompt with name '{prompt_data.name}' already exists"
                )

        # Validate project_id if provided
        if prompt_data.project_id:
            project = ProjectService.get_project_by_id(db, user, prompt_data.project_id)
            if not project:
                raise ValueError(f"Project with ID '{prompt_data.project_id}' not found")

        # Update fields
        if prompt_data.name is not None:
            prompt.name = prompt_data.name
        if prompt_data.description is not None:
            prompt.description = prompt_data.description
        if prompt_data.location is not None:
            prompt.location = prompt_data.location
        if prompt_data.project_id is not None:
            prompt.project_id = prompt_data.project_id
        if prompt_data.tags is not None:
            prompt.tags = prompt_data.tags

        db.commit()
        db.refresh(prompt)

        return prompt

    @staticmethod
    def delete_prompt(db: Session, user: User, prompt_id: str) -> bool:
        """Delete a prompt and all its versions"""
        prompt = PromptService.get_prompt_by_id(db, user, prompt_id)
        if not prompt:
            return False

        db.delete(prompt)
        db.commit()

        return True

    @staticmethod
    def create_version(
        db: Session, user: User, prompt_id: str, version_data: PromptVersionCreate
    ) -> Optional[PromptVersion]:
        """Create a new version for a prompt"""
        prompt = PromptService.get_prompt_by_id(db, user, prompt_id)
        if not prompt:
            return None

        # Get the next version number
        max_version = (
            db.query(func.max(PromptVersion.version_number))
            .filter(PromptVersion.prompt_id == prompt_id)
            .scalar()
            or 0
        )

        next_version = max_version + 1

        # Mark all existing versions as not current
        db.query(PromptVersion).filter(
            and_(PromptVersion.prompt_id == prompt_id, PromptVersion.is_current == True)
        ).update({"is_current": False})

        # Create new version
        new_version = PromptVersion(
            prompt_id=prompt_id,
            version_number=next_version,
            content=version_data.content,
            commit_message=version_data.commit_message,
            is_current=True,
        )

        db.add(new_version)
        db.flush()

        # Update prompt's current version
        prompt.current_version_id = new_version.id

        db.commit()
        db.refresh(new_version)

        return new_version

    @staticmethod
    def get_version(
        db: Session, user: User, prompt_id: str, version_number: int
    ) -> Optional[PromptVersion]:
        """Get a specific version of a prompt"""
        prompt = PromptService.get_prompt_by_id(db, user, prompt_id)
        if not prompt:
            return None

        return (
            db.query(PromptVersion)
            .filter(
                and_(
                    PromptVersion.prompt_id == prompt_id,
                    PromptVersion.version_number == version_number,
                )
            )
            .first()
        )

    @staticmethod
    def list_versions(db: Session, user: User, prompt_id: str) -> List[PromptVersion]:
        """List all versions of a prompt"""
        prompt = PromptService.get_prompt_by_id(db, user, prompt_id)
        if not prompt:
            return []

        return (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version_number.desc())
            .all()
        )

    @staticmethod
    def restore_version(
        db: Session,
        user: User,
        prompt_id: str,
        version_number: int,
        commit_message: Optional[str] = None,
    ) -> Optional[PromptVersion]:
        """Restore a prompt to a specific version by creating a new version with the old content"""
        # Get the version to restore
        version_to_restore = PromptService.get_version(
            db, user, prompt_id, version_number
        )
        if not version_to_restore:
            return None

        # Create new version with the old content
        restore_message = commit_message or f"Restored from version {version_number}"
        version_data = PromptVersionCreate(
            content=version_to_restore.content, commit_message=restore_message
        )

        return PromptService.create_version(db, user, prompt_id, version_data)

    @staticmethod
    def compare_versions(
        db: Session, user: User, prompt_id: str, version1: int, version2: int
    ) -> Optional[str]:
        """Compare two versions and return a diff"""
        v1 = PromptService.get_version(db, user, prompt_id, version1)
        v2 = PromptService.get_version(db, user, prompt_id, version2)

        if not v1 or not v2:
            return None

        # Generate unified diff
        diff = difflib.unified_diff(
            v1.content.splitlines(keepends=True),
            v2.content.splitlines(keepends=True),
            fromfile=f"Version {version1}",
            tofile=f"Version {version2}",
            lineterm="",
        )

        return "".join(diff)

    @staticmethod
    def search_prompts_by_content(
        db: Session, user: User, search_term: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[Prompt], int]:
        """Search prompts by content in their current versions"""
        # This is a simplified content search - in production you might want to use full-text search
        search_pattern = f"%{search_term}%"

        # Join with current versions to search content
        query = (
            db.query(Prompt)
            .join(PromptVersion, Prompt.current_version_id == PromptVersion.id)
            .filter(
                and_(
                    Prompt.user_id == user.id,
                    PromptVersion.content.ilike(search_pattern),
                )
            )
        )

        total = query.count()

        offset = (page - 1) * page_size
        prompts = (
            query.order_by(Prompt.updated_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return prompts, total

    @staticmethod
    def download_prompts(
        db: Session, user: User, download_params: PromptDownloadParams
    ) -> Tuple[List[Prompt], int, dict]:
        """Download prompts based on filters"""
        query = (
            db.query(Prompt)
            .options(joinedload(Prompt.project), joinedload(Prompt.current_version))
            .filter(Prompt.user_id == user.id)
        )

        filters_applied = {}

        # Apply filters
        if download_params.project_name:
            query = query.join(Project).filter(Project.name == download_params.project_name)
            filters_applied["project_name"] = download_params.project_name

        if download_params.directory:
            directory_term = f"%{download_params.directory}%"
            query = query.outerjoin(Project).filter(
                or_(
                    Project.directory.ilike(directory_term),
                    Prompt.location.ilike(directory_term),
                )
            )
            filters_applied["directory"] = download_params.directory

        if download_params.tags:
            from sqlalchemy import text
            for tag in download_params.tags:
                query = query.filter(
                    text(f"json_extract(tags, '$') LIKE '%\"{tag}\"%'")
                )
            filters_applied["tags"] = download_params.tags

        # Get total count
        total = query.count()

        # Get all matching prompts (no pagination for download)
        prompts = query.order_by(Prompt.updated_at.desc()).all()

        # If include_content is False, remove content from current_version
        if not download_params.include_content:
            for prompt in prompts:
                if prompt.current_version:
                    prompt.current_version.content = "[Content excluded]"

        return prompts, total, filters_applied
