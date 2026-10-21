from src.views.theme import Theme, ThemeComposite, ThemeLeaf


def test_theme_composite_applies_theme_to_every_component() -> None:
    composite = ThemeComposite(
        ThemeLeaf(lambda theme: f"header:{theme.value}"),
        ThemeLeaf(lambda theme: f"content:{theme.value}"),
    )

    assert composite.script(Theme.LIGHT) == "header:light\ncontent:light"


def test_theme_composite_accepts_components_after_creation() -> None:
    composite = ThemeComposite(ThemeLeaf(lambda theme: theme.value))
    composite.add(ThemeLeaf(lambda theme: f"saved:{theme.value}"))

    assert composite.script(Theme.DARK) == "dark\nsaved:dark"
