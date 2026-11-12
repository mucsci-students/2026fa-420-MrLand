"""Undo and redo stacks for configuration editor changes."""

from scheduler.config import CombinedConfig

from src.controllers.configuration_controller import (
    ConfigurationController,
    ConfigurationMemento,
)


class ConfigurationHistory:
    """Track editor snapshots independently of the editor's NiceGUI callbacks."""

    def __init__(self) -> None:
        self._undo: list[ConfigurationMemento] = []
        self._redo: list[ConfigurationMemento] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def record(self, snapshot: ConfigurationMemento) -> None:
        self._undo.append(snapshot)
        self._redo.clear()

    def undo(self, controller: ConfigurationController) -> CombinedConfig | None:
        if not self._undo or controller.configuration is None:
            return None

        current_snapshot = controller.create_memento()
        controller.restore_memento(self._undo[-1])
        self._undo.pop()
        self._redo.append(current_snapshot)
        return controller.configuration

    def redo(self, controller: ConfigurationController) -> CombinedConfig | None:
        if not self._redo or controller.configuration is None:
            return None

        current_snapshot = controller.create_memento()
        controller.restore_memento(self._redo[-1])
        self._redo.pop()
        self._undo.append(current_snapshot)
        return controller.configuration

    def snapshot(
        self,
    ) -> tuple[list[ConfigurationMemento], list[ConfigurationMemento]]:
        return self._undo.copy(), self._redo.copy()

    def restore(
        self,
        snapshot: tuple[list[ConfigurationMemento], list[ConfigurationMemento]],
    ) -> None:
        self._undo[:] = snapshot[0]
        self._redo[:] = snapshot[1]
