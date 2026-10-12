import pytest

import src.models.configuration_model as config_service
from src.models.configuration_model import validate_config_name


@pytest.fixture(autouse=True)
def no_existing_configs(monkeypatch):
    monkeypatch.setattr(config_service, "config_exists", lambda name: False)


def test_valid_name_is_trimmed():
    assert validate_config_name("  fall_2026  ") == "fall_2026"


def test_name_with_spaces_and_hyphens():
    assert validate_config_name("Fall 2026-draft") == "Fall 2026-draft"


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_name_rejected(name):
    with pytest.raises(ValueError, match="empty"):
        validate_config_name(name)


@pytest.mark.parametrize("name", ["../evil", "a/b", "name.json", "bad:name", "-leading"])
def test_unsafe_characters_rejected(name):
    with pytest.raises(ValueError):
        validate_config_name(name)


def test_too_long_name_rejected():
    with pytest.raises(ValueError):
        validate_config_name("a" * 65)


def test_existing_name_rejected(monkeypatch):
    monkeypatch.setattr(config_service, "config_exists", lambda name: name == "config1")
    with pytest.raises(ValueError, match="already exists"):
        validate_config_name("config1")