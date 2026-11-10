"""Observer-based propagation of configuration entity changes."""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
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


def publish_entity_changes(
    previous: CombinedConfig,
    current: CombinedConfig,
    subject: ConfigurationSubject,
) -> None:
    """Publish entity additions, renames, and deletions detected across one edit."""
    for entity_type, collection_name, name_attribute in (
        ("faculty", "faculty", "name"),
        ("room", "rooms", "name"),
        ("lab", "labs", "name"),
        ("course", "courses", "course_id"),
    ):
        old_entities = getattr(previous.config, collection_name)
        new_entities = getattr(current.config, collection_name)
        old_remaining = set(range(len(old_entities)))
        new_remaining = set(range(len(new_entities)))
        renames: list[tuple[str, str]] = []

        renames.extend(
            _match_entities(
                old_entities,
                new_entities,
                old_remaining,
                new_remaining,
                name_attribute,
                _entity_signature,
            )
        )
        renames.extend(
            _match_entities(
                old_entities,
                new_entities,
                old_remaining,
                new_remaining,
                name_attribute,
                partial(_stable_entity_signature, name_attribute=name_attribute),
            )
        )
        renames.extend(
            _match_entities(
                old_entities,
                new_entities,
                old_remaining,
                new_remaining,
                name_attribute,
                partial(_entity_name_key, name_attribute=name_attribute),
            )
        )
        if entity_type == "course":
            renames.extend(
                _match_entities(
                    old_entities,
                    new_entities,
                    old_remaining,
                    new_remaining,
                    name_attribute,
                    _course_section_key,
                )
            )
        if (
            len(old_remaining) == len(new_remaining) == 1
            and len(old_entities) == len(new_entities)
            and next(iter(old_remaining)) == next(iter(new_remaining))
        ):
            old_index = next(iter(old_remaining))
            new_index = next(iter(new_remaining))
            old_name = getattr(old_entities[old_index], name_attribute)
            new_name = getattr(new_entities[new_index], name_attribute)
            if old_name != new_name:
                renames.append((old_name, new_name))
            old_remaining.clear()
            new_remaining.clear()

        emitted_renames: set[tuple[str, str]] = set()
        for old_name, new_name in renames:
            rename_key = (_key(old_name), _key(new_name))
            if rename_key not in emitted_renames:
                subject.notify(EntityChangeEvent(entity_type, "renamed", old_name, new_name))
                emitted_renames.add(rename_key)

        for index in sorted(old_remaining):
            subject.notify(
                EntityChangeEvent(
                    entity_type,
                    "deleted",
                    getattr(old_entities[index], name_attribute),
                )
            )
        for index in sorted(new_remaining):
            subject.notify(
                EntityChangeEvent(
                    entity_type,
                    "created",
                    None,
                    getattr(new_entities[index], name_attribute),
                )
            )


def _match_entities(
    old_entities: Sequence[Any],
    new_entities: Sequence[Any],
    old_remaining: set[int],
    new_remaining: set[int],
    name_attribute: str,
    key: Callable[[Any], Any],
) -> list[tuple[str, str]]:
    old_by_key: dict[Any, list[int]] = {}
    for index in sorted(old_remaining):
        old_by_key.setdefault(key(old_entities[index]), []).append(index)
    new_by_key: dict[Any, list[int]] = {}
    for index in sorted(new_remaining):
        new_by_key.setdefault(key(new_entities[index]), []).append(index)

    renames = []
    for value, old_indices in old_by_key.items():
        new_indices = new_by_key.get(value, [])
        for old_index, new_index in zip(old_indices, new_indices):
            old_remaining.remove(old_index)
            new_remaining.remove(new_index)
            old_name = getattr(old_entities[old_index], name_attribute)
            new_name = getattr(new_entities[new_index], name_attribute)
            if old_name != new_name:
                renames.append((old_name, new_name))
    return renames


def _entity_signature(entity: Any) -> str:
    return json.dumps(entity.model_dump(mode="json"), sort_keys=True)


def _stable_entity_signature(entity: Any, *, name_attribute: str) -> str:
    payload = entity.model_dump(mode="json")
    payload.pop(name_attribute)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _entity_name_key(entity: Any, *, name_attribute: str) -> str:
    return _key(getattr(entity, name_attribute))


def _course_section_key(entity: Any) -> tuple[str, str | None] | tuple[str, int]:
    if entity.section_id is None:
        return "unidentified", id(entity)
    return "section", entity.section_id


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
