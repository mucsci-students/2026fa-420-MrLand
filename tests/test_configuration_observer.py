import pytest

from src.models.configuration_model import apply_configuration_change
from src.models.configuration_observer import (
    ConfigurationRelationshipObserver,
    ConfigurationSubject,
    EntityChangeEvent,
    capture_entity_snapshot,
    publish_entity_changes,
)
from tests.test_configuration import make_valid_config


def create_subject(config):
    subject = ConfigurationSubject()
    subject.subscribe(ConfigurationRelationshipObserver(config))
    return subject


def test_renaming_faculty_room_and_lab_updates_all_link_fields():
    config = make_valid_config()
    course = config.config.courses[0]
    faculty = config.config.faculty[0]
    faculty.room_preferences = {"Room 101": 8}
    faculty.lab_preferences = {"Lab 1": 7}
    subject = create_subject(config)

    faculty.name = "Dr. Jones"
    subject.notify(EntityChangeEvent("faculty", "renamed", "Dr. Adrian", "Dr. Jones"))
    config.config.rooms[0].name = "Room 202"
    subject.notify(EntityChangeEvent("room", "renamed", "Room 101", "Room 202"))
    config.config.labs[0].name = "Lab 2"
    subject.notify(EntityChangeEvent("lab", "renamed", "Lab 1", "Lab 2"))

    assert course.faculty == ["Dr. Jones"]
    assert course.room == ["Room 202"]
    assert course.lab == ["Lab 2"]
    assert faculty.room_preferences == {"Room 202": 8}
    assert faculty.lab_preferences == {"Lab 2": 7}


def test_publishing_configuration_changes_updates_subscribed_observer():
    config = make_valid_config()
    previous = capture_entity_snapshot(config)
    subject = create_subject(config)

    config.config.faculty[0].name = "Dr. Jones"
    publish_entity_changes(previous, config, subject)

    assert config.config.courses[0].faculty == ["Dr. Jones"]


def test_publishing_detects_renames_after_reordering_entities():
    config = make_valid_config()
    config.config.faculty.append(config.config.faculty[0].model_copy(update={"name": "Dr. Jones"}))
    previous = capture_entity_snapshot(config)
    subject = create_subject(config)

    config.config.faculty.reverse()
    config.config.faculty[1].name = "Dr. Smith"
    publish_entity_changes(previous, config, subject)

    assert config.config.courses[0].faculty == ["Dr. Smith"]


def test_publishing_reports_additions_without_misclassifying_existing_entities():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    config = make_valid_config()
    previous = capture_entity_snapshot(config)
    subject = ConfigurationSubject()
    recorder = Recorder()
    subject.subscribe(recorder)

    config.config.rooms.append(config.config.rooms[0].model_copy(update={"name": "Room 202"}))
    publish_entity_changes(previous, config, subject)

    assert recorder.events == [EntityChangeEvent("room", "created", None, "Room 202")]


def test_publishing_reports_entity_deletions():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    config = make_valid_config()
    previous = capture_entity_snapshot(config)
    subject = ConfigurationSubject()
    recorder = Recorder()
    subject.subscribe(recorder)

    config.config.rooms.clear()
    publish_entity_changes(previous, config, subject)

    assert recorder.events == [EntityChangeEvent("room", "deleted", "Room 101")]


def test_publishing_distinguishes_replacement_from_rename():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    config = make_valid_config()
    config.config.rooms.append(
        config.config.rooms[0].model_copy(update={"name": "Room 202", "capacity": 40})
    )
    previous = capture_entity_snapshot(config)
    subject = ConfigurationSubject()
    recorder = Recorder()
    subject.subscribe(recorder)

    config.config.rooms.pop(0)
    config.config.rooms.append(config.config.rooms[0].model_copy(update={"name": "Room 303"}))
    publish_entity_changes(previous, config, subject)

    assert recorder.events == [
        EntityChangeEvent("room", "deleted", "Room 101"),
        EntityChangeEvent("room", "created", None, "Room 303"),
    ]


def test_publishing_ignores_reordering_only():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    config = make_valid_config()
    config.config.rooms.append(config.config.rooms[0].model_copy(update={"name": "Room 202"}))
    config.config.faculty.append(config.config.faculty[0].model_copy(update={"name": "Dr. Jones"}))
    previous = capture_entity_snapshot(config)
    subject = ConfigurationSubject()
    recorder = Recorder()
    subject.subscribe(recorder)

    config.config.rooms.reverse()
    config.config.faculty.reverse()
    publish_entity_changes(previous, config, subject)

    assert recorder.events == []


def test_publishing_detects_rename_with_other_fields_changed():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    config = make_valid_config()
    previous = capture_entity_snapshot(config)
    subject = ConfigurationSubject()
    recorder = Recorder()
    subject.subscribe(recorder)

    config.config.rooms[0].name = "Room 202"
    config.config.rooms[0].capacity = 40
    publish_entity_changes(previous, config, subject)

    assert recorder.events == [EntityChangeEvent("room", "renamed", "Room 101", "Room 202")]


def test_renaming_a_course_id_updates_sections_conflicts_and_preferences():
    config = make_valid_config()
    course = config.config.courses[0]
    second_section = course.model_copy(update={"section_id": "002"})
    other_course = course.model_copy(
        update={"course_id": "MATH 100", "section_id": None, "conflicts": ["CS 121"]}
    )
    config.config.courses.extend([second_section, other_course])
    faculty = config.config.faculty[0]
    faculty.course_preferences = {"CS 121": 7}
    subject = create_subject(config)

    course.course_id = "CS 222"
    subject.notify(EntityChangeEvent("course", "renamed", "CS 121", "CS 222"))

    assert [item.course_id for item in config.config.courses] == [
        "CS 222",
        "CS 222",
        "MATH 100",
    ]
    assert other_course.conflicts == ["CS 222"]
    assert faculty.course_preferences == {"CS 222": 7}


def test_deleting_entities_removes_their_references():
    config = make_valid_config()
    course = config.config.courses[0]
    faculty = config.config.faculty[0]
    course.conflicts = ["MATH 100"]
    faculty.course_preferences = {"MATH 100": 7}
    faculty.room_preferences = {"Room 101": 8}
    faculty.lab_preferences = {"Lab 1": 9}
    subject = create_subject(config)

    room = config.config.rooms.pop()
    subject.notify(EntityChangeEvent("room", "deleted", room.name))
    lab = config.config.labs.pop()
    subject.notify(EntityChangeEvent("lab", "deleted", lab.name))
    course_id = "MATH 100"
    subject.notify(EntityChangeEvent("course", "deleted", course_id))
    assert faculty.course_preferences == {}
    assert faculty.room_preferences == {}
    assert faculty.lab_preferences == {}
    config.config.faculty.remove(faculty)
    subject.notify(EntityChangeEvent("faculty", "deleted", faculty.name))

    assert course.faculty is None
    assert course.room == []
    assert course.lab == []
    assert course.conflicts == []
    assert config.config.faculty == []


def test_deleting_one_section_keeps_references_while_another_remains():
    config = make_valid_config()
    course = config.config.courses[0]
    second_section = course.model_copy(update={"section_id": "002"})
    config.config.courses.append(second_section)
    subject = create_subject(config)

    config.config.courses.remove(course)
    subject.notify(EntityChangeEvent("course", "deleted", course.course_id))

    assert config.config.courses[0].course_id == "CS 121"


def test_course_rename_rejects_conflicting_preference_scores_without_mutating():
    config = make_valid_config()
    faculty = config.config.faculty[0]
    faculty.course_preferences = {"CS 121": 6, "CS 222": 8}
    subject = create_subject(config)

    def rename_course():
        config.config.courses[0].course_id = "CS 222"
        subject.notify(EntityChangeEvent("course", "renamed", "CS 121", "CS 222"))

    with pytest.raises(ValueError, match="preference conflicts"):
        apply_configuration_change(
            config,
            rename_course,
            has_valid_baseline=True,
        )

    assert config.config.courses[0].course_id == "CS 121"
    assert faculty.course_preferences == {"CS 121": 6, "CS 222": 8}


def test_subject_subscribes_and_unsubscribes_observers():
    class Recorder:
        def __init__(self):
            self.events = []

        def on_entity_change(self, event):
            self.events.append(event)

    subject = ConfigurationSubject()
    observer = Recorder()
    event = EntityChangeEvent("faculty", "deleted", "Dr. Adrian")

    subject.subscribe(observer)
    subject.subscribe(observer)
    subject.notify(event)
    subject.unsubscribe(observer)
    subject.unsubscribe(observer)
    subject.notify(event)

    assert observer.events == [event]
