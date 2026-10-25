"""Coordinates configuration creation, validation, loading, saving, and edits.

Used by: GUI."""

import copy
from collections.abc import Callable
from pathlib import Path
from dataclasses import dataclass
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

T = TypeVar("T")


@dataclass(frozen=True)
class ConfigurationMemento:
    configuration: CombinedConfig
    has_valid_configuration: bool


class ConfigurationController:

    def __init__(self) -> None:
        self.config_service = ConfigService()
        self.configuration: CombinedConfig | None = None
        self._has_valid_configuration = False

    def create_memento(self) -> ConfigurationMemento:
        '''
        Captures the current config to restore if required later

        Returns: memento holding a deep copy, so edits to the open config 
        don't change the snapshot

        Raises: ValueError on 'No Config Open'
        '''
        if self.configuration is None:
            raise ValueError("No configuration has been created or loaded.")
        
        return ConfigurationMemento(
            copy.deepcopy(self.configuration),
            self._has_valid_configuration,
        )

    def restore_memento(self, memento: ConfigurationMemento) -> None:
        '''Replace the open config with the saved snapshot'''

        self.configuration = copy.deepcopy(memento.configuration)
        self._has_valid_configuration = memento.has_valid_configuration

    def new_configuration(self) -> CombinedConfig:
        '''
        Unsaved changes are not saved, Views should confirm with User

        Returns: the new empty draft
        '''
        self.configuration = create_draft_config()
        self._has_valid_configuration = False

        return self.configuration

    def save_configuration(self, config_name: str) -> None:
        '''
        Saves the open configuration under config_name. It validates first and
        raises ConfigValidationError (with the list of problems) instead of
        writing an invalid file. Raises ValueError if nothing is open.
        '''
        if self.configuration is None:
            raise ValueError("No configuration has been created.")
        
        problems = self.validate_configuration()

        if problems:
            raise ConfigValidationError(problems)
        
        self.config_service.save(self.configuration, config_name)

    def export_configuration(self, file_name: str) -> tuple[bytes, str, str]:
        """
        Builds a downloadable JSON copy of the open Config
        Return validated configuration JSON and download metadata.
        """

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

        content = self.configuration.model_dump_json(indent=4).encode("utf-8")
        return content, file_name, "application/json"
    
    def load_configuration(self, config_name: str) -> CombinedConfig:

        '''
        Loads a saved configuration and makes it the open one. A loaded file has
        already passed validation, so _has_valid_configuration is set to True,
        which means later edits that make it invalid will be rolled back.

        Raises:
        FileNotFound - No saved config has that name
        ConfigLoadError - the file exists but can't be parsed or fails validation.

        Returns Loaded Config
        '''

        self.configuration = self.config_service.load(config_name)
        self._has_valid_configuration = True
        return self.configuration
    
    
    # Load and validate a configuration from an uploaded JSON file
    def load_uploaded_configuration(self, content: bytes) -> CombinedConfig:
        configuration = self.config_service.load_uploaded(content)

        self.configuration = configuration
        self._has_valid_configuration = True

        return self.configuration

    def list_names(self) -> list[str]:
        return self.config_service.list_names()

    def validate_configuration(self) -> list[ValidationProblem]:
        '''
        Checks the open config against scheduler's rules to 
        report problems.

        Returns: 
        List of problems
        or empty for valid

        Raises:
        ValueError: No config is open 
        '''
        if self.configuration is None:
            raise ValueError("No configuration has been created or loaded.")
        
        return validate_config(self.configuration)

    def apply_change(
        self, mutation: Callable[[], T]
    ) -> tuple[bool, list[ValidationProblem]]:
        '''
        Run edit against open config under validation rules

        Routing edits here keeps validation in one place
        Rolls changes back if invalid

        Returns:
        Tuple (accepted, problems)

        Raises: 
        ValueError - No config is open
        '''
        if self.configuration is None:
            raise ValueError("No configuration has been created or loaded.")

        accepted, problems, _ = apply_configuration_change(
            self.configuration,
            mutation,
            has_valid_baseline=self._has_valid_configuration,
        )

        if not problems:
            self._has_valid_configuration = True

        return accepted, problems
