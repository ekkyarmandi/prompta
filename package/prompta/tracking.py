"""Prompt tracking functionality with auto-detection and explicit naming.

This module provides enhanced prompt tracking that automatically:
1. Detects context (function, file, line) for grouping
2. Requires explicit prompt name/id for identification
3. Creates versions when content changes
4. Avoids duplicate versions
5. Links prompts across different invocations
6. Supports file-based prompt management
7. Supports version-specific prompt loading
"""

import hashlib
import inspect
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import Prompt, PromptVersion
from .client import PromptaClient
from .config import Config
from .exceptions import NotFoundError


class TrackedPrompt(Prompt):
    """Enhanced Prompt class with auto-detection, explicit naming, file support, and version loading."""

    # Class-level registry to track prompts across invocations
    # Structure: {tracking_key: TrackedPrompt_instance}
    _registry: Dict[str, "TrackedPrompt"] = {}

    def __init__(
        self,
        content: Optional[str] = None,
        prompt_name: Optional[str] = None,
        name: Optional[str] = None,
        location: Optional[str] = None,
        version: Optional[Union[str, int]] = None,
        project_id: Optional[str] = None,
        auto_detect_context: bool = True,
        auto_sync_file: bool = True,
        client: Optional[PromptaClient] = None,
        **kwargs,
    ):
        """Initialize a tracked prompt with auto-detection, file support, and version loading.

        Args:
            content: Prompt content (if None, will try to read from location or version)
            prompt_name: Explicit name/identifier for this prompt (preferred)
            name: Alternative to prompt_name for backward compatibility
            location: File path to read/write prompt content
            version: Specific version to load (e.g., 1, "v1", "latest", "current")
            project_id: Optional project to associate with
            auto_detect_context: Whether to auto-detect calling context
            auto_sync_file: Whether to automatically sync with file
            client: Optional client instance
            **kwargs: Additional prompt attributes
        """
        # Handle backward compatibility and parameter resolution
        self._prompt_name = prompt_name or name
        if not self._prompt_name:
            raise ValueError("Either 'prompt_name' or 'name' must be provided")

        self._location = location
        self._auto_sync_file = auto_sync_file
        self._auto_detect_context = auto_detect_context
        self._context_info = self._detect_context() if auto_detect_context else {}
        self._target_version = version
        self._is_version_specific = version is not None

        # Generate unique tracking key combining context and prompt name
        self._tracking_key = self._generate_tracking_key()

        # Resolve content: provided > version > file > empty
        self._content = self._resolve_content(content)

        # Initialize parent with computed name and location
        super().__init__(
            client=client,
            name=self._tracking_key,
            location=location or self._generate_location(),
            project_id=project_id,
            description=kwargs.get(
                "description", f"Auto-tracked prompt: {self._prompt_name}"
            ),
            tags=kwargs.get("tags", ["auto-tracked", self._prompt_name]),
            **{
                k: v
                for k, v in kwargs.items()
                if k not in ["location", "description", "tags"]
            },
        )

        # Handle tracking logic (skip for version-specific loads)
        if not self._is_version_specific:
            self._handle_tracking()
        else:
            self._handle_version_specific_loading()

    def _resolve_content(self, provided_content: Optional[str]) -> str:
        """Resolve content from provided content, version, or file."""
        if provided_content is not None:
            # Content provided directly
            if (
                self._location
                and self._auto_sync_file
                and not self._is_version_specific
            ):
                # Write content to file (but not for version-specific loads)
                self._write_to_file(provided_content)
            return provided_content
        elif self._target_version is not None:
            # Load specific version (will be handled in _handle_version_specific_loading)
            return ""  # Placeholder, will be set later
        elif self._location:
            # Try to read from file
            return self._read_from_file()
        else:
            # No content, no version, and no file
            raise ValueError(
                "Either 'content', 'version', or 'location' must be provided"
            )

    def _parse_version_identifier(self, version: Union[str, int]) -> Union[int, str]:
        """Parse version identifier into standard format.

        Args:
            version: Version identifier (1, "1", "v1", "latest", "current")

        Returns:
            Standardized version (int for numeric, str for special)
        """
        if isinstance(version, int):
            return version

        if isinstance(version, str):
            # Handle special versions
            if version.lower() in ["latest", "current"]:
                return "latest"

            # Handle "v1", "v2" format
            if version.lower().startswith("v") and version[1:].isdigit():
                return int(version[1:])

            # Handle pure numeric strings
            if version.isdigit():
                return int(version)

            # Handle semantic versions like "1.0", "2.1"
            if re.match(r"^\d+\.\d+$", version):
                # For now, treat semantic versions as strings
                return version

        raise ValueError(
            f"Invalid version format: {version}. Use int, 'v1', 'latest', or 'current'"
        )

    def _handle_version_specific_loading(self):
        """Handle loading a specific version of the prompt."""
        try:
            # Try to load existing prompt with this tracking key
            existing_prompt = Prompt.get(self._tracking_key)

            # Copy basic data from existing prompt
            self.id = existing_prompt.id
            self.created_at = existing_prompt.created_at
            self.updated_at = existing_prompt.updated_at

            # Load the specific version
            parsed_version = self._parse_version_identifier(self._target_version)

            if parsed_version == "latest":
                # Load current version
                self.current_version = existing_prompt.current_version
                if self.current_version:
                    self._content = self.current_version.content
                else:
                    raise ValueError("No current version found")
                self._log_action(f"Loaded latest version for {self._tracking_key}")
            else:
                # Load specific version number
                target_version = self.get_version(parsed_version)
                self.current_version = target_version
                self._content = target_version.content
                self._log_action(
                    f"Loaded version {parsed_version} for {self._tracking_key}"
                )

        except NotFoundError:
            raise NotFoundError(
                f"Prompt '{self._tracking_key}' not found. Cannot load version {self._target_version}"
            )

    def _read_from_file(self) -> str:
        """Read content from file."""
        if not self._location:
            raise ValueError("No location specified for file reading")

        try:
            file_path = Path(self._location)
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8").strip()
                self._log_action(f"Read content from {self._location}")
                return content
            else:
                raise FileNotFoundError(f"Prompt file not found: {self._location}")
        except Exception as e:
            raise ValueError(f"Failed to read prompt from {self._location}: {e}")

    def _write_to_file(self, content: str):
        """Write content to file."""
        if not self._location:
            return

        try:
            file_path = Path(self._location)
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            self._log_action(f"Wrote content to {self._location}")
        except Exception as e:
            self._log_action(f"Failed to write to {self._location}: {e}")

    def _detect_context(self) -> Dict[str, Any]:
        """Detect the calling context for auto-tracking."""
        frame = inspect.currentframe()
        context = {}

        try:
            # Go up the stack to find the calling function (skip __init__)
            caller_frame = frame.f_back.f_back
            if caller_frame:
                context.update(
                    {
                        "function": caller_frame.f_code.co_name,
                        "filename": Path(caller_frame.f_code.co_filename).stem,
                        "line_number": caller_frame.f_lineno,
                        "module": caller_frame.f_globals.get("__name__", "unknown"),
                    }
                )
        finally:
            del frame

        return context

    def _generate_tracking_key(self) -> str:
        """Generate unique tracking key combining context and prompt name."""
        if self._auto_detect_context and self._context_info:
            # Format: filename_function_promptname
            context_part = f"{self._context_info.get('filename', 'unknown')}_{self._context_info.get('function', 'unknown')}"
            return f"{context_part}_{self._prompt_name}"
        else:
            # Just use prompt name if no context detection
            return self._prompt_name

    def _generate_location(self) -> str:
        """Generate location path based on context and prompt name."""
        if self._location:
            return self._location
        elif self._auto_detect_context and self._context_info:
            filename = self._context_info.get("filename", "unknown")
            function = self._context_info.get("function", "unknown")
            return f"tracked/{filename}/{function}/{self._prompt_name}.txt"
        else:
            return f"tracked/{self._prompt_name}.txt"

    def _content_hash(self) -> str:
        """Generate hash of content for duplicate detection."""
        return hashlib.sha256(self._content.encode()).hexdigest()[:12]

    def _handle_tracking(self):
        """Handle the tracking logic for this prompt."""
        if self._tracking_key in TrackedPrompt._registry:
            # Existing tracked prompt
            existing = TrackedPrompt._registry[self._tracking_key]
            self._update_from_existing(existing)

            # Check if content changed and create version if needed
            if self._content != existing.content:
                self._create_new_version()
            else:
                self._content = existing.content  # Keep existing content
        else:
            # New tracked prompt
            self._create_or_load_prompt()
            TrackedPrompt._registry[self._tracking_key] = self

    def _update_from_existing(self, existing: "TrackedPrompt"):
        """Update this instance with data from existing tracked prompt."""
        self.id = existing.id
        self.created_at = existing.created_at
        self.updated_at = existing.updated_at
        self.current_version = existing.current_version

        # Update registry reference to point to this instance
        TrackedPrompt._registry[self._tracking_key] = self

    def _create_or_load_prompt(self):
        """Create a new prompt or load existing one from API."""
        try:
            # Try to load existing prompt with this tracking key
            existing_prompt = Prompt.get(self._tracking_key)

            # Copy data from existing prompt
            self.id = existing_prompt.id
            self.created_at = existing_prompt.created_at
            self.updated_at = existing_prompt.updated_at
            self.current_version = existing_prompt.current_version

            # Check if we need a new version
            if existing_prompt.content != self._content:
                self._create_new_version()

        except NotFoundError:
            # Create new prompt
            commit_msg = self._generate_commit_message("Initial version")
            self.save(content=self._content, commit_message=commit_msg)
            self._log_action(f"Created new tracked prompt: {self._tracking_key}")

    def _create_new_version(self):
        """Create a new version if content is different."""
        if not self.id:
            raise ValueError("Cannot create version for prompt without ID")

        # Check if this content already exists in any version
        if not self._is_content_duplicate():
            commit_msg = self._generate_commit_message("Content updated")
            version = self.create_version(
                content=self._content, commit_message=commit_msg
            )
            self._log_action(
                f"Created version {version.version_number} for {self._tracking_key}"
            )

            # Update file if auto-sync is enabled
            if self._location and self._auto_sync_file:
                self._write_to_file(self._content)
        else:
            self._log_action(
                f"Content unchanged for {self._tracking_key} - no new version created"
            )

    def _is_content_duplicate(self) -> bool:
        """Check if the current content already exists in any version."""
        try:
            versions = self.get_versions()
            return any(version.content == self._content for version in versions)
        except Exception:
            return False

    def _generate_commit_message(self, action: str) -> str:
        """Generate a commit message with context information."""
        file_info = f" (from {self._location})" if self._location else ""
        version_info = (
            f" (version {self._target_version})" if self._is_version_specific else ""
        )
        if self._auto_detect_context and self._context_info:
            context = f"{self._context_info['filename']}.{self._context_info['function']}:{self._context_info['line_number']}"
            return f"{action} from {context}{file_info}{version_info} (hash: {self._content_hash()})"
        else:
            return f"{action}{file_info}{version_info} (hash: {self._content_hash()})"

    def _log_action(self, message: str):
        """Log tracking actions."""
        print(f"📝 {message}")

    def update_content(self, new_content: str, commit_message: Optional[str] = None):
        """Update prompt content and optionally sync to file.

        Args:
            new_content: New prompt content
            commit_message: Optional commit message
        """
        if self._is_version_specific:
            raise ValueError(
                "Cannot update content of version-specific prompt. Load without version parameter to update."
            )

        if new_content != self._content:
            self._content = new_content

            # Update file if auto-sync enabled
            if self._location and self._auto_sync_file:
                self._write_to_file(new_content)

            # Create new version in API
            if self.id:
                if not self._is_content_duplicate():
                    commit_msg = commit_message or self._generate_commit_message(
                        "Content updated via update_content"
                    )
                    version = self.create_version(
                        content=new_content, commit_message=commit_msg
                    )
                    self._log_action(
                        f"Updated content and created version {version.version_number}"
                    )

    def reload_from_file(self):
        """Reload content from file and create new version if changed."""
        if not self._location:
            raise ValueError("No file location specified")

        if self._is_version_specific:
            raise ValueError(
                "Cannot reload version-specific prompt from file. Load without version parameter to reload."
            )

        new_content = self._read_from_file()
        if new_content != self._content:
            self._content = new_content
            if self.id and not self._is_content_duplicate():
                commit_msg = self._generate_commit_message("Reloaded from file")
                version = self.create_version(
                    content=new_content, commit_message=commit_msg
                )
                self._log_action(
                    f"Reloaded from file and created version {version.version_number}"
                )

    def load_version(self, version: Union[str, int]) -> "TrackedPrompt":
        """Load a specific version of this prompt.

        Args:
            version: Version to load (e.g., 1, "v1", "latest")

        Returns:
            New TrackedPrompt instance with the specified version
        """
        return TrackedPrompt(
            prompt_name=self._prompt_name,
            version=version,
            project_id=self.project_id,
            auto_detect_context=False,  # Use same tracking key
            client=self._client,
        )

    @property
    def content(self) -> str:
        """Get the tracked content."""
        return self._content

    @property
    def prompt_name(self) -> str:
        """Get the prompt name."""
        return self._prompt_name

    @property
    def tracking_key(self) -> str:
        """Get the full tracking key."""
        return self._tracking_key

    @property
    def context_info(self) -> Dict[str, Any]:
        """Get the detected context information."""
        return self._context_info.copy()

    @property
    def file_location(self) -> Optional[str]:
        """Get the file location."""
        return self._location

    @property
    def target_version(self) -> Optional[Union[str, int]]:
        """Get the target version if this is a version-specific load."""
        return self._target_version

    @property
    def is_version_specific(self) -> bool:
        """Check if this is a version-specific prompt load."""
        return self._is_version_specific

    @classmethod
    def create_tracked(
        cls,
        content: Optional[str] = None,
        prompt_name: Optional[str] = None,
        name: Optional[str] = None,
        location: Optional[str] = None,
        version: Optional[Union[str, int]] = None,
        project_id: Optional[str] = None,
        auto_detect_context: bool = True,
        auto_sync_file: bool = True,
        client: Optional[PromptaClient] = None,
        **kwargs,
    ) -> "TrackedPrompt":
        """Create a tracked prompt with explicit naming, file support, and version loading.

        This is the main entry point for creating tracked prompts.

        Args:
            content: Prompt content (if None, will read from location or version)
            prompt_name: Explicit name/identifier for this prompt (preferred)
            name: Alternative to prompt_name for backward compatibility
            location: File path to read/write prompt content
            version: Specific version to load (e.g., 1, "v1", "latest")
            project_id: Optional project ID
            auto_detect_context: Whether to auto-detect calling context
            auto_sync_file: Whether to automatically sync with file
            client: Optional client
            **kwargs: Additional prompt attributes

        Returns:
            TrackedPrompt instance
        """
        return cls(
            content=content,
            prompt_name=prompt_name,
            name=name,
            location=location,
            version=version,
            project_id=project_id,
            auto_detect_context=auto_detect_context,
            auto_sync_file=auto_sync_file,
            client=client,
            **kwargs,
        )

    @classmethod
    def get_tracked_prompts(cls) -> Dict[str, "TrackedPrompt"]:
        """Get all currently tracked prompts."""
        return cls._registry.copy()

    @classmethod
    def get_tracked_prompt(cls, tracking_key: str) -> Optional["TrackedPrompt"]:
        """Get a specific tracked prompt by tracking key."""
        return cls._registry.get(tracking_key)

    @classmethod
    def clear_registry(cls):
        """Clear the tracking registry (useful for testing)."""
        cls._registry.clear()

    @classmethod
    def show_tracking_info(cls):
        """Show information about all tracked prompts."""
        if not cls._registry:
            print("No tracked prompts in registry")
            return

        print(f"Currently tracking {len(cls._registry)} prompts:")
        for key, prompt in cls._registry.items():
            versions_count = len(prompt.get_versions()) if prompt.id else 0
            print(f"  🎯 {key}")
            print(f"     Prompt Name: {prompt.prompt_name}")
            print(f"     Content Hash: {prompt._content_hash()}")
            print(f"     Versions: {versions_count}")
            print(f"     File Location: {prompt.file_location or 'None'}")
            print(f"     Version Specific: {prompt.is_version_specific}")
            if prompt.target_version:
                print(f"     Target Version: {prompt.target_version}")
            if prompt.context_info:
                context = prompt.context_info
                print(
                    f"     Context: {context.get('filename')}.{context.get('function')}:{context.get('line_number')}"
                )
            print()

    def __repr__(self) -> str:
        file_info = f", file='{self._location}'" if self._location else ""
        version_info = (
            f", version={self._target_version}" if self._is_version_specific else ""
        )
        return f"<TrackedPrompt(key='{self._tracking_key}', name='{self._prompt_name}'{file_info}{version_info}, hash='{self._content_hash()}')>"


# Convenience function for the main use case
def tracked_prompt(
    content: Optional[str] = None,
    prompt_name: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    version: Optional[Union[str, int]] = None,
    project_id: Optional[str] = None,
    **kwargs,
) -> TrackedPrompt:
    """Create a tracked prompt with auto-detection, file support, and version loading.

    This is the main function users should use for tracking prompts.

    Args:
        content: Prompt content (if None, will read from location or version)
        prompt_name: Name/identifier for this specific prompt (preferred)
        name: Alternative to prompt_name for backward compatibility
        location: File path to read/write prompt content
        version: Specific version to load (e.g., 1, "v1", "latest")
        project_id: Optional project ID
        **kwargs: Additional prompt attributes

    Returns:
        TrackedPrompt instance

    Example:
        # Load latest version
        prompt = tracked_prompt(name="assistant")

        # Load specific version
        prompt = tracked_prompt(name="assistant", version="v1")
        prompt = tracked_prompt(name="assistant", version=2)

        # Read from file
        prompt = tracked_prompt(name="assistant", location="prompt.txt")

        # Load version with fallback to file
        prompt = tracked_prompt(name="assistant", version="v1", location="prompt.txt")
    """
    return TrackedPrompt.create_tracked(
        content=content,
        prompt_name=prompt_name,
        name=name,
        location=location,
        version=version,
        project_id=project_id,
        auto_detect_context=True,
        auto_sync_file=True,
        **kwargs,
    )
