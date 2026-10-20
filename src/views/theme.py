"""Composable theme operations for the NiceGUI application."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum


class Theme(Enum):
    """Available visual themes supported by the application."""

    DARK = "dark"
    LIGHT = "light"


class ThemeComponent(ABC):
    """A theme operation that can be composed with other operations."""

    @abstractmethod
    def script(self, theme: Theme) -> str:
        """Return the JavaScript needed to apply this theme operation."""


class ThemeLeaf(ThemeComponent):
    """A single theme operation represented by a JavaScript factory."""

    def __init__(self, script_factory: Callable[[Theme], str]) -> None:
        """Store the function that builds this leaf's theme script."""
        self._script_factory = script_factory

    def script(self, theme: Theme) -> str:
        """Build the JavaScript for this individual theme operation."""
        return self._script_factory(theme)


class ThemeComposite(ThemeComponent):
    """A group of theme operations that share the component interface."""

    def __init__(self, *components: ThemeComponent) -> None:
        """Initialize the composite with the theme operations to apply."""
        self._components = list(components)

    def add(self, component: ThemeComponent) -> None:
        """Append another operation to the composite."""
        self._components.append(component)

    def script(self, theme: Theme) -> str:
        """Combine each child operation into one executable JavaScript script."""
        return "\n".join(component.script(theme) for component in self._components)
