"""Composable theme operations for the NiceGUI application."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum


class Theme(Enum):
    DARK = "dark"
    LIGHT = "light"


class ThemeComponent(ABC):
    """A theme operation that can be composed with other operations."""

    @abstractmethod
    def script(self, theme: Theme) -> str:
        """Return the JavaScript needed to apply this theme operation."""


class ThemeLeaf(ThemeComponent):
    def __init__(self, script_factory: Callable[[Theme], str]) -> None:
        self._script_factory = script_factory

    def script(self, theme: Theme) -> str:
        return self._script_factory(theme)


class ThemeComposite(ThemeComponent):
    def __init__(self, *components: ThemeComponent) -> None:
        self._components = list(components)

    def add(self, component: ThemeComponent) -> None:
        self._components.append(component)

    def script(self, theme: Theme) -> str:
        return "\n".join(component.script(theme) for component in self._components)
