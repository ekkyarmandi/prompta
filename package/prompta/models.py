"""Data models and interface objects for the Prompta API.

These classes provide a clean interface for interacting with Prompta projects and prompts
without needing to handle HTTP requests or API details directly.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .client import PromptaClient
from .config import Config, ConfigManager
from .exceptions import NotFoundError, ValidationError


def _get_api_key() -> str:
    """Get API key from various sources using ConfigManager."""
    config_manager = ConfigManager()
    config_manager.load()
    api_key = config_manager.get_api_key()

    if not api_key:
        raise ValueError(
            "API key not found. Please set PROMPTA_API_KEY environment variable "
            "or configure it in ~/.prompta file"
        )

    return api_key


class BaseModel:
    """Base class for all Prompta models."""

    def __init__(
        self, client: Optional[PromptaClient] = None, config: Optional[Config] = None
    ):
        """Initialize with optional client and config."""
        if client:
            self._client = client
        else:
            if not config:
                config = Config()
            api_key = _get_api_key()
            self._client = PromptaClient(api_key, config)

    @classmethod
    def _from_dict(
        cls, data: Dict[str, Any], client: Optional[PromptaClient] = None
    ) -> "BaseModel":
        """Create instance from API response data."""
        instance = cls(client=client)
        for key, value in data.items():
            if key == "created_at" or key == "updated_at":
                # Handle datetime strings
                if isinstance(value, str):
                    try:
                        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        pass
            setattr(instance, key, value)
        return instance


class Project(BaseModel):
    """Interface for Prompta projects."""

    def __init__(
        self,
        client: Optional[PromptaClient] = None,
        config: Optional[Config] = None,
        **kwargs,
    ):
        """Initialize a Project instance.

        Args:
            client: Optional PromptaClient instance
            config: Optional Config instance
            **kwargs: Project attributes (id, name, description, etc.)
        """
        super().__init__(client, config)

        # Initialize attributes
        self.id: Optional[str] = kwargs.get("id")
        self.name: str = kwargs.get("name", "")
        self.description: Optional[str] = kwargs.get("description")
        self.tags: List[str] = kwargs.get("tags", [])
        self.created_at: Optional[datetime] = kwargs.get("created_at")
        self.updated_at: Optional[datetime] = kwargs.get("updated_at")
        self.is_active: bool = kwargs.get("is_active", True)
        self.is_public: bool = kwargs.get("is_public", False)

        # Handle datetime fields
        for date_field in ["created_at", "updated_at"]:
            if date_field in kwargs and isinstance(kwargs[date_field], str):
                try:
                    setattr(
                        self,
                        date_field,
                        datetime.fromisoformat(
                            kwargs[date_field].replace("Z", "+00:00")
                        ),
                    )
                except (ValueError, AttributeError):
                    pass

    def save(self) -> "Project":
        """Save the project (create if new, update if existing)."""
        if self.id:
            # Update existing project
            update_data = {
                "name": self.name,
                "description": self.description,
                "tags": self.tags,
                "is_active": self.is_active,
                "is_public": self.is_public,
            }
            response = self._client.update_project(self.id, update_data)
        else:
            # Create new project
            create_data = {
                "name": self.name,
                "description": self.description,
                "tags": self.tags,
                "is_public": self.is_public,
            }
            response = self._client.create_project(create_data)

        # Update instance with response data
        for key, value in response.items():
            if key in ["created_at", "updated_at"] and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            setattr(self, key, value)

        return self

    def delete(self) -> None:
        """Delete the project."""
        if not self.id:
            raise ValueError("Cannot delete project without ID")
        self._client.delete_project(self.id)

    def get_prompts(self) -> List["Prompt"]:
        """Get all prompts in this project."""
        if not self.id:
            raise ValueError("Cannot get prompts for project without ID")

        prompts_data = self._client.get_prompts()
        # Filter by project_id
        project_prompts = [p for p in prompts_data if p.get("project_id") == self.id]
        return [
            Prompt._from_dict(prompt_data, self._client)
            for prompt_data in project_prompts
        ]

    @classmethod
    def create(
        cls,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
        client: Optional[PromptaClient] = None,
    ) -> "Project":
        """Create a new project.

        Args:
            name: Project name
            description: Optional project description
            tags: Optional list of tags
            is_public: Whether project is public
            client: Optional PromptaClient instance

        Returns:
            Created Project instance
        """
        project = cls(
            client=client,
            name=name,
            description=description,
            tags=tags or [],
            is_public=is_public,
        )
        return project.save()

    @classmethod
    def get(cls, identifier: str, client: Optional[PromptaClient] = None) -> "Project":
        """Get a project by ID or name.

        Args:
            identifier: Project ID or name
            client: Optional PromptaClient instance

        Returns:
            Project instance
        """
        if not client:
            api_key = _get_api_key()
            client = PromptaClient(api_key, Config())

        try:
            # Try by ID first
            if len(identifier) == 36 and identifier.count("-") == 4:
                data = client.get_project_by_id(identifier)
            else:
                data = client.get_project_by_name(identifier)
            return cls._from_dict(data, client)
        except NotFoundError:
            raise NotFoundError(f"Project '{identifier}' not found")

    @classmethod
    def list(
        cls,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        client: Optional[PromptaClient] = None,
    ) -> List["Project"]:
        """List projects with optional filtering.

        Args:
            query: Search term for name or description
            tags: Filter by tags
            page: Page number
            page_size: Items per page
            client: Optional PromptaClient instance

        Returns:
            List of Project instances
        """
        if not client:
            api_key = _get_api_key()
            client = PromptaClient(api_key, Config())

        response = client.get_projects(
            query=query, tags=tags, page=page, page_size=page_size
        )
        return [
            cls._from_dict(project_data, client)
            for project_data in response.get("projects", [])
        ]

    def __repr__(self) -> str:
        return f"<Project(id='{self.id}', name='{self.name}')>"


class PromptVersion:
    """Represents a version of a prompt."""

    def __init__(self, **kwargs):
        self.id: str = kwargs.get("id", "")
        self.version_number: int = kwargs.get("version_number", 1)
        self.content: str = kwargs.get("content", "")
        self.commit_message: Optional[str] = kwargs.get("commit_message")
        self.created_at: Optional[datetime] = kwargs.get("created_at")
        self.is_current: bool = kwargs.get("is_current", False)

        # Handle datetime field
        if "created_at" in kwargs and isinstance(kwargs["created_at"], str):
            try:
                self.created_at = datetime.fromisoformat(
                    kwargs["created_at"].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "PromptVersion":
        """Create instance from API response data."""
        return cls(**data)

    def __repr__(self) -> str:
        return f"<PromptVersion(version={self.version_number}, is_current={self.is_current})>"


class Prompt(BaseModel):
    """Interface for Prompta prompts."""

    def __init__(
        self,
        client: Optional[PromptaClient] = None,
        config: Optional[Config] = None,
        **kwargs,
    ):
        """Initialize a Prompt instance.

        Args:
            client: Optional PromptaClient instance
            config: Optional Config instance
            **kwargs: Prompt attributes (id, name, content, etc.)
        """
        super().__init__(client, config)

        # Initialize attributes
        self.id: Optional[str] = kwargs.get("id")
        self.name: str = kwargs.get("name", "")
        self.description: Optional[str] = kwargs.get("description")
        self.location: str = kwargs.get("location", "")
        self.project_id: Optional[str] = kwargs.get("project_id")
        self.tags: List[str] = kwargs.get("tags", [])
        self.is_public: bool = kwargs.get("is_public", False)
        self.created_at: Optional[datetime] = kwargs.get("created_at")
        self.updated_at: Optional[datetime] = kwargs.get("updated_at")
        self.current_version: Optional[PromptVersion] = None

        # Handle datetime fields
        for date_field in ["created_at", "updated_at"]:
            if date_field in kwargs and isinstance(kwargs[date_field], str):
                try:
                    setattr(
                        self,
                        date_field,
                        datetime.fromisoformat(
                            kwargs[date_field].replace("Z", "+00:00")
                        ),
                    )
                except (ValueError, AttributeError):
                    pass

        # Handle current_version if provided
        if "current_version" in kwargs and kwargs["current_version"]:
            self.current_version = PromptVersion._from_dict(kwargs["current_version"])

    @property
    def content(self) -> str:
        """Get the current version's content."""
        if self.current_version:
            return self.current_version.content
        return ""

    def save(
        self, content: Optional[str] = None, commit_message: Optional[str] = None
    ) -> "Prompt":
        """Save the prompt (create if new, update if existing).

        Args:
            content: Prompt content (required for new prompts)
            commit_message: Optional commit message for version
        """
        if self.id:
            # Update existing prompt
            update_data = {
                "name": self.name,
                "description": self.description,
                "location": self.location,
                "project_id": self.project_id,
                "tags": self.tags,
                "is_public": self.is_public,
            }
            response = self._client.update_prompt(self.id, update_data)

            # Create new version if content provided
            if content:
                version_data = {"content": content, "commit_message": commit_message}
                version_response = self._client.create_version(self.id, version_data)
                self.current_version = PromptVersion._from_dict(version_response)
        else:
            # Create new prompt
            if not content:
                raise ValueError("Content is required for new prompts")

            create_data = {
                "name": self.name,
                "description": self.description,
                "location": self.location,
                "project_id": self.project_id,
                "tags": self.tags,
                "content": content,
                "commit_message": commit_message,
                "is_public": self.is_public,
            }
            response = self._client.create_prompt(create_data)

        # Update instance with response data
        for key, value in response.items():
            if key == "current_version" and value:
                self.current_version = PromptVersion._from_dict(value)
            elif key in ["created_at", "updated_at"] and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
                setattr(self, key, value)
            else:
                setattr(self, key, value)

        return self

    def delete(self) -> None:
        """Delete the prompt."""
        if not self.id:
            raise ValueError("Cannot delete prompt without ID")
        self._client.delete_prompt(self.id)

    def create_version(
        self, content: str, commit_message: Optional[str] = None
    ) -> PromptVersion:
        """Create a new version of this prompt.

        Args:
            content: Version content
            commit_message: Optional commit message

        Returns:
            Created PromptVersion instance
        """
        if not self.id:
            raise ValueError("Cannot create version for prompt without ID")

        version_data = {"content": content, "commit_message": commit_message}
        response = self._client.create_version(self.id, version_data)
        version = PromptVersion._from_dict(response)

        # Update current version if this is the new current one
        if version.is_current:
            self.current_version = version

        return version

    def get_versions(self) -> List[PromptVersion]:
        """Get all versions of this prompt."""
        if not self.id:
            raise ValueError("Cannot get versions for prompt without ID")

        versions_data = self._client.get_versions(self.id)
        return [
            PromptVersion._from_dict(version_data) for version_data in versions_data
        ]

    def get_version(self, version_number: int) -> PromptVersion:
        """Get a specific version of this prompt."""
        if not self.id:
            raise ValueError("Cannot get version for prompt without ID")

        version_data = self._client.get_version(self.id, version_number)
        return PromptVersion._from_dict(version_data)

    def restore_version(self, version_number: int) -> "Prompt":
        """Restore this prompt to a specific version."""
        if not self.id:
            raise ValueError("Cannot restore version for prompt without ID")

        response = self._client.restore_version(self.id, version_number)

        # Update instance with response data
        for key, value in response.items():
            if key == "current_version" and value:
                self.current_version = PromptVersion._from_dict(value)
            elif key in ["created_at", "updated_at"] and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
                setattr(self, key, value)
            else:
                setattr(self, key, value)

        return self

    @classmethod
    def create(
        cls,
        name: str,
        content: str,
        location: str,
        description: Optional[str] = None,
        project_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        commit_message: Optional[str] = None,
        is_public: bool = False,
        client: Optional[PromptaClient] = None,
    ) -> "Prompt":
        """Create a new prompt.

        Args:
            name: Prompt name
            content: Initial prompt content
            location: File location/path
            description: Optional description
            project_id: Optional project ID
            tags: Optional list of tags
            commit_message: Optional commit message
            is_public: Whether prompt is public
            client: Optional PromptaClient instance

        Returns:
            Created Prompt instance
        """
        prompt = cls(
            client=client,
            name=name,
            description=description,
            location=location,
            project_id=project_id,
            tags=tags or [],
            is_public=is_public,
        )
        return prompt.save(content=content, commit_message=commit_message)

    @classmethod
    def get(
        cls,
        identifier: str,
        project_id: Optional[str] = None,
        client: Optional[PromptaClient] = None,
    ) -> "Prompt":
        """Get a prompt by ID or name.

        Args:
            identifier: Prompt ID or name
            project_id: Optional project ID to filter by (for name conflicts)
            client: Optional PromptaClient instance

        Returns:
            Prompt instance
        """
        if not client:
            api_key = _get_api_key()
            client = PromptaClient(api_key, Config())

        try:
            data = client.get_prompt(identifier, project_id)
            return cls._from_dict(data, client)
        except NotFoundError:
            raise NotFoundError(f"Prompt '{identifier}' not found")

    @classmethod
    def list(
        cls,
        tags: Optional[List[str]] = None,
        location: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        client: Optional[PromptaClient] = None,
    ) -> List["Prompt"]:
        """List prompts with optional filtering.

        Args:
            tags: Filter by tags
            location: Filter by location
            project_id: Filter by project ID
            limit: Maximum number of results
            offset: Number of results to skip
            client: Optional PromptaClient instance

        Returns:
            List of Prompt instances
        """
        if not client:
            api_key = _get_api_key()
            client = PromptaClient(api_key, Config())

        prompts_data = client.get_prompts(
            tags=tags, location=location, limit=limit, offset=offset
        )
        prompts = [cls._from_dict(prompt_data, client) for prompt_data in prompts_data]

        # Filter by project_id if specified (client method doesn't support it)
        if project_id:
            prompts = [p for p in prompts if p.project_id == project_id]

        return prompts

    @classmethod
    def search(
        cls, query: str, client: Optional[PromptaClient] = None
    ) -> List["Prompt"]:
        """Search prompts by content.

        Args:
            query: Search query
            client: Optional PromptaClient instance

        Returns:
            List of matching Prompt instances
        """
        if not client:
            api_key = _get_api_key()
            client = PromptaClient(api_key, Config())

        prompts_data = client.search_prompts(query)
        return [cls._from_dict(prompt_data, client) for prompt_data in prompts_data]

    def __repr__(self) -> str:
        return (
            f"<Prompt(id='{self.id}', name='{self.name}', location='{self.location}')>"
        )
