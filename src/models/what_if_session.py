"""Isolated configuration snapshots for What-If schedule analysis."""

import copy
from dataclasses import dataclass

from scheduler.config import CombinedConfig


@dataclass(frozen=True)
class ConfigurationMemento:
    """The baseline configuration to restore when a What-If session is discarded."""

    configuration: CombinedConfig
    name: str


class WhatIfSession:
    """Keep temporary edits separate from their source configuration."""

    def __init__(self, configuration: CombinedConfig, name: str) -> None:
        self._baseline = ConfigurationMemento(copy.deepcopy(configuration), name)
        self.configuration = copy.deepcopy(configuration)

    @property
    def name(self) -> str:
        return self._baseline.name

    @property
    def has_changes(self) -> bool:
        return self.configuration.model_dump() != self._baseline.configuration.model_dump()

    def generation_snapshot(self) -> CombinedConfig:
        """Return a copy so background generation cannot observe later edits."""
        return copy.deepcopy(self.configuration)

    def discard(self) -> None:
        """Restore the initial configuration without mutating its source."""
        self.configuration = copy.deepcopy(self._baseline.configuration)
