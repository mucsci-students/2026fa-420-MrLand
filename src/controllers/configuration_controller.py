"""Coordinates configuration creation, validation, loading, saving, and edits.

Used by: GUI."""

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import TypeVar

from scheduler.config import CombinedConfig

from src.models.configuration_model import (
    ConfigService,
    ConfigValidationError,
    ValidationProblem,
    apply_configuration_change,
    create_draft_config,
    validate_config,
)
from src.models.configuration_observer import (
    ConfigurationRelationshipObserver,
    ConfigurationSubject,
    capture_entity_snapshot,
    publish_entity_changes,
)
from src.models.quality_grade_settings_repository import (
    load_quality_grade_settings,
    save_quality_grade_settings,
)
from src.models.quality_grading import QualityGradeSettings, settings_from_document

T = TypeVar("T")


@dataclass(frozen=True)
class ConfigurationMemento:
    configuration: CombinedConfig
    has_valid_configuration: bool


class ConfigurationController:
    def __init__(self, configuration: CombinedConfig | None = None) -> None:
        self.config_service = ConfigService()
        self.configuration = configuration
        self.quality_grade_settings = QualityGradeSettings()
        self._has_valid_configuration = configuration is not None and not validate_config(
            configuration
        )
        self._lock = RLock()
        self._change_subject = ConfigurationSubject()
        self._observed_configuration: CombinedConfig | None = None
        self._relationship_observer: ConfigurationRelationshipObserver | None = None

    def create_memento(self) -> ConfigurationMemento:
        """
        Captures the current config to restore if required later

        Returns: memento holding a deep copy, so edits to the open config
        don't change the snapshot

        Raises: ValueError on 'No Config Open'
        """
        with self._lock:
            if self.configuration is None:
                raise ValueError("No configuration has been created or loaded.")

            return ConfigurationMemento(
                copy.deepcopy(self.configuration),
                self._has_valid_configuration,
            )

    def restore_memento(self, memento: ConfigurationMemento) -> None:
        """Replace the open config with the saved snapshot"""

        with self._lock:
            self.configuration = copy.deepcopy(memento.configuration)
            self._has_valid_configuration = memento.has_valid_configuration

    def new_configuration(self) -> CombinedConfig:
        """
        Unsaved changes are not saved, Views should confirm with User

        Returns: the new empty draft
        """
        with self._lock:
            self.configuration = create_draft_config()
            self.quality_grade_settings = QualityGradeSettings()
            self._has_valid_configuration = False

            return self.configuration

    def save_configuration(self, config_name: str) -> None:
        """
        Saves the open configuration under config_name. It validates first and
        raises ConfigValidationError (with the list of problems) instead of
        writing an invalid file. Raises ValueError if nothing is open.
        """
        with self._lock:
            if self.configuration is None:
                raise ValueError("No configuration has been created.")

            problems = self.validate_configuration()

            if problems:
                raise ConfigValidationError(problems)

            self.config_service.save(
                self.configuration,
                config_name,
                self.quality_grade_settings,
            )
            save_quality_grade_settings(config_name, self.quality_grade_settings)

    def export_configuration(self, file_name: str) -> tuple[bytes, str, str]:
        """
        Builds a downloadable JSON copy of the open Config
        Return validated configuration JSON and download metadata.
        """

        with self._lock:
            if self.configuration is None:
                raise ValueError("No configuration has been created.")

            problems = self.validate_configuration()

            if problems:
                raise ConfigValidationError(problems)

            file_name = Path(file_name.strip()).name

            if not file_name or file_name.startswith("."):
                raise ValueError("Please enter a valid file name.")

            if Path(file_name).suffix.lower() != ".json":
                file_name = f"{file_name}.json"

            document = self.configuration.model_dump(mode="json")
            if self.quality_grade_settings != QualityGradeSettings():
                document["quality_grade_settings"] = self.quality_grade_settings.model_dump(
                    mode="json"
                )
            content = json.dumps(document, indent=4).encode("utf-8")
            return content, file_name, "application/json"

    def load_configuration(self, config_name: str) -> CombinedConfig:
        """
        Loads a saved configuration and makes it the open one. A loaded file has
        already passed validation, so _has_valid_configuration is set to True,
        which means later edits that make it invalid will be rolled back.

        Raises:
        FileNotFound - No saved config has that name
        ConfigLoadError - the file exists but can't be parsed or fails validation.

        Returns Loaded Config
        """

        with self._lock:
            quality_grade_settings = load_quality_grade_settings(config_name)
            self.configuration = self.config_service.load(config_name)
            self.quality_grade_settings = quality_grade_settings
            self._has_valid_configuration = True
            return self.configuration

    # Load and validate a configuration from an uploaded JSON file
    def load_uploaded_configuration(
        self,
        content: bytes,
        config_name: str | None = None,
    ) -> CombinedConfig:
        quality_grade_settings = settings_from_document(json.loads(content))
        configuration = self.config_service.load_uploaded(content)
        with self._lock:
            self.configuration = configuration
            self.quality_grade_settings = quality_grade_settings
            if config_name:
                save_quality_grade_settings(config_name, quality_grade_settings)
            self._has_valid_configuration = True
            return self.configuration

    def set_quality_grade_settings(
        self,
        config_name: str,
        settings: QualityGradeSettings,
    ) -> None:
        """Update the active profile and persist it for future schedule analysis."""
        with self._lock:
            save_quality_grade_settings(config_name, settings)
            self.quality_grade_settings = settings

    def list_names(self) -> list[str]:
        return self.config_service.list_names()

    def validate_configuration(self) -> list[ValidationProblem]:
        """
        Checks the open config against scheduler's rules to
        report problems.

        Returns:
        List of problems
        or empty for valid

        Raises:
        ValueError: No config is open
        """
        with self._lock:
            if self.configuration is None:
                raise ValueError("No configuration has been created or loaded.")

            return validate_config(self.configuration)

    def apply_change(self, mutation: Callable[[], T]) -> tuple[bool, list[ValidationProblem]]:
        """
        Run edit against open config under validation rules

        Routing edits here keeps validation in one place
        Rolls changes back if invalid

        Returns:
        Tuple (accepted, problems)

        Raises:
        ValueError - No config is open
        """
        with self._lock:
            if self.configuration is None:
                raise ValueError("No configuration has been created or loaded.")

            configuration = self.configuration
            previous_entities = capture_entity_snapshot(configuration)
            if self._observed_configuration is not configuration:
                if self._relationship_observer is not None:
                    self._change_subject.unsubscribe(self._relationship_observer)
                self._relationship_observer = ConfigurationRelationshipObserver(configuration)
                self._change_subject.subscribe(self._relationship_observer)
                self._observed_configuration = configuration

            accepted, problems, _ = apply_configuration_change(
                configuration,
                mutation,
                has_valid_baseline=self._has_valid_configuration,
                after_mutation=lambda _previous, current: publish_entity_changes(
                    previous_entities,
                    current,
                    self._change_subject,
                ),
            )

            if not problems:
                self._has_valid_configuration = True

            return accepted, problems
