"""Observer-based propagation of configuration entity changes."""

from dataclasses import dataclass
from typing import Any, Literal, Protocol, overload

from scheduler.config import CombinedConfig

EntityType = Literal["course", "faculty", "lab", "room"]
ChangeAction = Literal["created", "renamed", "deleted"]


@dataclass(frozen=True)
class EntityChangeEvent:
    entity_type: EntityType
    action: ChangeAction
    old_name: str | None = None
    new_name: str | None = None


@dataclass(frozen=True)
class EntityIdentity:
    entity: Any
    name: str


@dataclass(frozen=True)
class ConfigurationEntitySnapshot:
    faculty: tuple[EntityIdentity, ...]
    rooms: tuple[EntityIdentity, ...]
    labs: tuple[EntityIdentity, ...]
    courses: tuple[EntityIdentity, ...]


class ConfigurationObserver(Protocol):
    def on_entity_change(self, event: EntityChangeEvent) -> None: ...


class ConfigurationSubject:
    """Publish entity changes to observers of a single configuration."""

    def __init__(self) -> None:
        self._observers: list[ConfigurationObserver] = []

    def subscribe(self, observer: ConfigurationObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: ConfigurationObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, event: EntityChangeEvent) -> None:
        for observer in tuple(self._observers):
            observer.on_entity_change(event)


class ConfigurationRelationshipObserver:
    """Keep string-based relationships in sync with entity names."""

    def __init__(self, config: CombinedConfig) -> None:
        self._config = config

    def on_entity_change(self, event: EntityChangeEvent) -> None:
        if event.action == "created":
            return
        if event.action == "renamed":
            if event.old_name is None or event.new_name is None:
                raise ValueError("A rename event must include both names.")
            self._rename_references(event.entity_type, event.old_name, event.new_name)
        else:
            if event.old_name is None:
                raise ValueError("A deletion event must include the old name.")
            self._remove_references(event.entity_type, event.old_name)

    def _rename_references(self, entity_type: EntityType, old_name: str, new_name: str) -> None:
        section = self._config.config
        old_key = _key(old_name)

        if entity_type == "faculty":
            for course in section.courses:
                course.faculty = _rename_list(course.faculty, old_key, new_name)
            return

        if entity_type == "room":
            for faculty in section.faculty:
                _validate_mapping_key_rename(faculty.room_preferences, old_key, new_name, "room")
            for course in section.courses:
                course.room = _rename_list(course.room, old_key, new_name)
            for faculty in section.faculty:
                faculty.room_preferences = _rename_mapping_key(
                    faculty.room_preferences, old_key, new_name, "room"
                )
            return

        if entity_type == "lab":
            for faculty in section.faculty:
                _validate_mapping_key_rename(faculty.lab_preferences, old_key, new_name, "lab")
            for course in section.courses:
                course.lab = _rename_list(course.lab, old_key, new_name)
            for faculty in section.faculty:
                faculty.lab_preferences = _rename_mapping_key(
                    faculty.lab_preferences, old_key, new_name, "lab"
                )
            return

        self._rename_course_id(old_name, new_name)

    def _rename_course_id(self, old_name: str, new_name: str) -> None:
        section = self._config.config
        old_key = _key(old_name)
        new_key = _key(new_name)
        moving_courses = [course for course in section.courses if _key(course.course_id) == old_key]
        target_courses = [
            course
            for course in section.courses
            if _key(course.course_id) == new_key and _key(course.course_id) != old_key
        ]

        for moving_course in moving_courses:
            if any(course.section_id == moving_course.section_id for course in target_courses):
                raise ValueError(
                    f"Renaming '{old_name}' to '{new_name}' would duplicate a course section."
                )

        for course in section.courses:
            new_course_id = new_name if _key(course.course_id) == old_key else course.course_id
            if _key(new_course_id) == new_key and any(
                _key(conflict) in {old_key, new_key} for conflict in course.conflicts
            ):
                raise ValueError(
                    f"Renaming '{old_name}' to '{new_name}' would make "
                    f"'{new_course_id}' conflict with itself."
                )

        for faculty in section.faculty:
            _validate_mapping_key_rename(faculty.course_preferences, old_key, new_name, "course")

        for course in moving_courses:
            course.course_id = new_name
        for course in section.courses:
            course.conflicts = _rename_list(course.conflicts, old_key, new_name)
        for faculty in section.faculty:
            faculty.course_preferences = _rename_mapping_key(
                faculty.course_preferences, old_key, new_name, "course"
            )

    def _remove_references(self, entity_type: EntityType, old_name: str) -> None:
        section = self._config.config
        old_key = _key(old_name)

        if entity_type == "faculty":
            for course in section.courses:
                remaining_faculty = _remove_list(course.faculty, old_key)
                course.faculty = remaining_faculty or None
            return

        if entity_type == "room":
            for course in section.courses:
                course.room = _remove_list(course.room, old_key)
            for faculty in section.faculty:
                faculty.room_preferences = _remove_mapping_key(faculty.room_preferences, old_key)
            return

        if entity_type == "lab":
            for course in section.courses:
                course.lab = _remove_list(course.lab, old_key)
            for faculty in section.faculty:
                faculty.lab_preferences = _remove_mapping_key(faculty.lab_preferences, old_key)
            return

        if any(_key(course.course_id) == old_key for course in section.courses):
            return
        for course in section.courses:
            course.conflicts = _remove_list(course.conflicts, old_key)
        for faculty in section.faculty:
            faculty.course_preferences = _remove_mapping_key(faculty.course_preferences, old_key)


def capture_entity_snapshot(config: CombinedConfig) -> ConfigurationEntitySnapshot:
    return ConfigurationEntitySnapshot(
        faculty=tuple(EntityIdentity(item, item.name) for item in config.config.faculty),
        rooms=tuple(EntityIdentity(item, item.name) for item in config.config.rooms),
        labs=tuple(EntityIdentity(item, item.name) for item in config.config.labs),
        courses=tuple(EntityIdentity(item, item.course_id) for item in config.config.courses),
    )


def publish_entity_changes(
    previous: ConfigurationEntitySnapshot,
    current: CombinedConfig,
    subject: ConfigurationSubject,
) -> None:
    """Publish entity changes using the identities captured before an edit."""
    for entity_type, old_entities, new_entities, name_attribute in (
        ("faculty", previous.faculty, current.config.faculty, "name"),
        ("room", previous.rooms, current.config.rooms, "name"),
        ("lab", previous.labs, current.config.labs, "name"),
        ("course", previous.courses, current.config.courses, "course_id"),
    ):
        old_by_identity = {id(item.entity): item for item in old_entities}
        current_ids = {id(item) for item in new_entities}
        for item in old_entities:
            if id(item.entity) not in current_ids:
                subject.notify(EntityChangeEvent(entity_type, "deleted", item.name))
        for entity in new_entities:
            old_item = old_by_identity.get(id(entity))
            new_name = getattr(entity, name_attribute)
            if old_item is None:
                subject.notify(EntityChangeEvent(entity_type, "created", None, new_name))
            elif old_item.name != new_name:
                subject.notify(EntityChangeEvent(entity_type, "renamed", old_item.name, new_name))


def _key(value: str) -> str:
    return value.casefold()


@overload
def _rename_list[T: str](values: list[T], old_key: str, new_value: T) -> list[T]: ...


@overload
def _rename_list(values: None, old_key: str, new_value: str) -> None: ...


def _rename_list[T: str](values: list[T] | None, old_key: str, new_value: T) -> list[T] | None:
    if values is None:
        return None

    renamed: list[T] = []
    new_key = _key(new_value)
    seen_new_value = False
    for value in values:
        value_key = _key(value)
        if value_key == old_key or value_key == new_key:
            if not seen_new_value:
                renamed.append(new_value)
                seen_new_value = True
        else:
            renamed.append(value)
    return renamed


@overload
def _remove_list[T: str](values: list[T], old_key: str) -> list[T]: ...


@overload
def _remove_list(values: None, old_key: str) -> None: ...


def _remove_list[T: str](values: list[T] | None, old_key: str) -> list[T] | None:
    if values is None:
        return None
    return [value for value in values if _key(value) != old_key]


def _validate_mapping_key_rename[K: str](
    values: dict[K, int], old_key: str, new_value: K, entity_label: str
) -> None:
    new_key = _key(new_value)
    matching_values = [value for key, value in values.items() if _key(key) in {old_key, new_key}]
    if len(set(matching_values)) <= 1:
        return
    raise ValueError(
        f"Cannot rename this {entity_label}: its preference conflicts "
        f"with the existing '{new_value}' preference."
    )


def _rename_mapping_key[K: str](
    values: dict[K, int], old_key: str, new_value: K, entity_label: str
) -> dict[K, int]:
    _validate_mapping_key_rename(values, old_key, new_value, entity_label)
    renamed: dict[K, int] = {}
    new_key = _key(new_value)
    for key, value in values.items():
        if _key(key) in {old_key, new_key}:
            destination = new_value
        else:
            destination = key
        renamed[destination] = value
    return renamed


def _remove_mapping_key[K: str](values: dict[K, int], old_key: str) -> dict[K, int]:
    return {key: value for key, value in values.items() if _key(key) != old_key}
