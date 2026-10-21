"""Builds and launches the NiceGUI scheduling application.

Used by: GUI."""

import os
from collections.abc import Callable

from nicegui import ui

from src.views.ai_assistant import scheduler_ai_assistant
from src.views.configuration_editor import configuration_editor, controller
from src.views.schedule_generator import schedule_generator
from src.views.schedule_viewer import schedule_viewer
from src.views.theme import Theme, ThemeComposite, ThemeLeaf

BACKGROUND = "#101820"
ACCENT = "#75e6da"


def build_app() -> None:
    """Configure the shared theme styles and assemble the application pages."""
    ui.colors(primary=ACCENT, dark=BACKGROUND)
    # Choose the saved theme first, falling back to the browser's system preference.
    ui.add_head_html(
        """
        <script>
            const savedTheme = localStorage.getItem('mrland-theme');
            document.documentElement.dataset.theme =
                savedTheme === 'light' || savedTheme === 'dark'
                    ? savedTheme
                    : window.matchMedia('(prefers-color-scheme: light)').matches
                        ? 'light'
                        : 'dark';
        </script>
        <style>
            /* Shared dark-theme tokens and base component styling. */
            :root {
                --app-background: #101820;
                --app-foreground: #d8e7e8;
                --text-primary: #ffffff;
                --text-muted: #9fb2b8;
                --accent-color: #75e6da;
                --border-color: #29404b;
                --border-strong: #45616b;
                --surface: #182630;
                --surface-raised: #17232b;
                --surface-hover: #1c3039;
            }
            /* Light mode overrides the shared color tokens. */
            :root[data-theme="light"] {
                --app-background: #f1f5f9;
                --app-foreground: #26384d;
                --text-primary: #17324f;
                --text-muted: #53677d;
                --accent-color: #234f78;
                --surface-accent: #dce8f4;
                --border-color: #d1dce8;
                --border-strong: #b4c5d6;
                --surface: #ffffff;
                --surface-raised: #ffffff;
                --surface-hover: #e7eef5;
            }
            body, .q-layout, .q-page {
                background: var(--app-background);
                color: var(--app-foreground);
            }
            /* Shared styling for tabs, fields, and configuration panels. */
            .q-tab { min-height: 56px; color: var(--app-foreground) !important; text-transform: none; }
            .q-tab__label { color: var(--app-foreground) !important; font-weight: 600; }
            .q-tab--active, .q-tab--active .q-tab__label { color: var(--accent-color) !important; }
            .q-tab__indicator { background: var(--accent-color) !important; }
            .q-field__label, .q-field__native, .q-field__input, .q-placeholder,
            .q-select__dropdown-icon, .q-table th, .q-table td,
            .q-expansion-item__toggle-icon { color: var(--app-foreground) !important; }
            .configuration-panel { color: var(--app-foreground); }
            .configuration-panel .q-checkbox__label { color: var(--app-foreground) !important; }
            .mandatory-days .q-chip--selected { background: var(--app-foreground) !important; }
            .mandatory-days .q-chip--selected .q-chip__content { color: var(--app-background) !important; }
            .mandatory-days .q-menu .q-checkbox__bg { border-color: var(--border-strong) !important; }
            .mandatory-days .q-menu .q-checkbox__inner--truthy .q-checkbox__bg { background: var(--accent-color) !important; border-color: var(--accent-color) !important; }
            .mandatory-days .q-menu .q-checkbox__svg { color: var(--app-background) !important; }
            .q-field--outlined .q-field__control:before { border-color: var(--border-strong); }
            .q-field--outlined.q-field--focused .q-field__control:after { border-color: var(--accent-color); }
            /* Light-mode corrections for components that carry Quasar dark classes. */
            html[data-theme="light"] body,
            html[data-theme="light"] .q-layout,
            html[data-theme="light"] .q-page {
                background: var(--app-background) !important;
                color: var(--app-foreground);
            }
            html[data-theme="light"] [class~="text-white"],
            html[data-theme="light"] [class~="text-[#d8e7e8]"],
            html[data-theme="light"] [class~="text-gray-300"] {
                color: var(--text-primary) !important;
            }
            html[data-theme="light"] [class~="text-[#101820]"] {
                color: var(--text-primary) !important;
            }
            html[data-theme="light"] [class~="text-[#9fb2b8]"],
            html[data-theme="light"] [class~="text-gray-400"] {
                color: var(--text-muted) !important;
            }
            html[data-theme="light"] [class~="text-[#75e6da]"] {
                color: var(--accent-color) !important;
            }
            html[data-theme="light"] [class~="bg-[#101820]"] {
                background-color: var(--app-background) !important;
            }
            html[data-theme="light"] [class~="bg-[#17232b]"],
            html[data-theme="light"] [class~="bg-[#182630]"] {
                background-color: var(--surface) !important;
            }
            html[data-theme="light"] [class~="bg-[#75e6da]"] {
                background-color: var(--surface-accent) !important;
            }
            html[data-theme="light"] [class~="border-[#29404b]"],
            html[data-theme="light"] [class~="border-[#45616b]"],
            html[data-theme="light"] [class~="border-b-[#29404b]"] {
                border-color: var(--border-color) !important;
            }
            html[data-theme="light"] .q-field--dark,
            html[data-theme="light"] .q-field--dark .q-field__label,
            html[data-theme="light"] .q-field--dark .q-field__native,
            html[data-theme="light"] .q-field--dark .q-field__input,
            html[data-theme="light"] .q-checkbox--dark .q-checkbox__label {
                color: var(--app-foreground) !important;
            }
            html[data-theme="light"] .q-menu {
                background: var(--surface) !important;
                color: var(--app-foreground) !important;
            }
            html[data-theme="light"] .mandatory-days .q-chip--selected {
                background: var(--surface-accent) !important;
            }
            html[data-theme="light"] .mandatory-days .q-chip--selected .q-chip__content {
                color: var(--text-primary) !important;
            }
            html[data-theme="light"] .mandatory-days .q-menu .q-checkbox__svg {
                color: var(--text-primary) !important;
            }
            @layer quasar_importants {
                html[data-theme="light"] .text-white,
                html[data-theme="light"] [class~="text-[#d8e7e8]"],
                html[data-theme="light"] [class~="text-[#101820]"],
                html[data-theme="light"] .text-gray-300 {
                    color: var(--text-primary) !important;
                }
                html[data-theme="light"] [class~="text-[#9fb2b8]"],
                html[data-theme="light"] .text-gray-400 {
                    color: var(--text-muted) !important;
                }
                html[data-theme="light"] [class~="text-[#75e6da]"],
                html[data-theme="light"] .text-primary {
                    color: var(--accent-color) !important;
                }
                html[data-theme="light"] header.q-header {
                    background-color: var(--app-background) !important;
                    color: var(--text-primary) !important;
                }
                html[data-theme="light"] .q-tab,
                html[data-theme="light"] .q-tab__label,
                html[data-theme="light"] .q-tab__icon {
                    color: var(--text-primary) !important;
                }
                html[data-theme="light"] .q-tab--active,
                html[data-theme="light"] .q-tab--active .q-tab__label,
                html[data-theme="light"] .q-tab--active .q-tab__icon {
                    color: var(--accent-color) !important;
                }
                html[data-theme="light"] .q-tab__indicator {
                    background-color: var(--accent-color) !important;
                }
                html[data-theme="light"] .q-btn--unelevated {
                    background-color: var(--accent-color) !important;
                    color: #ffffff !important;
                }
                html[data-theme="light"] .q-btn.bg-primary {
                    background-color: var(--accent-color) !important;
                    color: #ffffff !important;
                }
                html[data-theme="light"] .q-btn--unelevated .q-btn__content,
                html[data-theme="light"] .q-btn--unelevated .q-icon,
                html[data-theme="light"] .q-btn.bg-primary .q-btn__content,
                html[data-theme="light"] .q-btn.bg-primary .q-icon {
                    color: #ffffff !important;
                }
                html[data-theme="light"] .q-btn--outline {
                    color: var(--accent-color) !important;
                }
                html[data-theme="light"] .q-checkbox__bg {
                    background-color: transparent !important;
                    border-color: var(--border-strong) !important;
                }
                html[data-theme="light"] .q-checkbox__inner--truthy .q-checkbox__bg {
                    background-color: #234f78 !important;
                    border-color: #234f78 !important;
                    opacity: 1 !important;
                }
                html[data-theme="light"] .q-checkbox__inner--truthy {
                    color: #234f78 !important;
                }
                html[data-theme="light"] .q-checkbox__inner--truthy .q-checkbox__svg {
                    color: #ffffff !important;
                }
                html[data-theme="light"] .q-menu .q-item,
                html[data-theme="light"] .q-menu .q-item__label {
                    color: var(--app-foreground) !important;
                }
                html[data-theme="light"] .q-menu .q-item:hover {
                    background-color: var(--surface-hover) !important;
                }
                html[data-theme="light"] .q-menu .q-item--active {
                    background-color: var(--surface-accent) !important;
                }
            }
        </style>
        """
    )

    # Apply each theme to the document, header, and page content as one operation.
    theme = ThemeComposite(
        ThemeLeaf(
            lambda mode: (
                f"document.documentElement.dataset.theme = '{mode.value}'; "
                f"localStorage.setItem('mrland-theme', '{mode.value}');"
            )
        ),
        ThemeLeaf(
            lambda mode: (
                "document.querySelector('[data-theme-region=\"header\"]').dataset.theme "
                f"= '{mode.value}';"
            )
        ),
        ThemeLeaf(
            lambda mode: (
                "document.querySelector('[data-theme-region=\"content\"]').dataset.theme "
                f"= '{mode.value}';"
            )
        ),
    )

    # Read the current browser theme, apply its opposite, and update the button label.
    async def toggle_theme() -> None:
        current = await ui.run_javascript(
            "document.documentElement.dataset.theme"
        )
        next_theme = Theme.DARK if current == Theme.LIGHT.value else Theme.LIGHT
        await ui.run_javascript(theme.script(next_theme))
        toggle_button.set_text(f"{next_theme.value.title()} Mode")

    # Keep the button label aligned with the saved or system-selected theme on connect.
    async def sync_theme_label() -> None:
        current = await ui.run_javascript(
            "document.documentElement.dataset.theme"
        )
        toggle_button.set_text(f"{Theme(current).value.title()} Mode")

    # Shared application header and theme control.
    with ui.header().props("data-theme-region=header").classes(
        "border-b border-[#29404b] bg-[#101820] px-6 py-4"
    ):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("calendar_month", size="32px").classes("text-[#75e6da]")
                with ui.column().classes("gap-0"):
                    ui.label("Scheduler").classes("text-lg font-semibold text-white")
            toggle_button = ui.button(
                "Dark Mode", icon="contrast", on_click=toggle_theme
            ).props("unelevated aria-label=Toggle color theme").classes(
                "bg-[#75e6da] text-[#101820]"
            )
            ui.context.client.on_connect(sync_theme_label)

    # Main tabbed area containing configuration, generation, and schedule views.
    with ui.column().props("data-theme-region=content").classes(
        "mx-auto w-full max-w-7xl gap-0 px-6 py-8"
    ):
        tabs = ui.tabs(value="configuration").classes("w-full border-b border-[#29404b]")
        with tabs:
            ui.tab("configuration", label="Configuration Editor", icon="tune")
            ui.tab("generator", label="Schedule Generator", icon="auto_awesome")
            ui.tab("viewer", label="Schedule Viewer", icon="calendar_view_week")

        editor_refresh: Callable[[], None]
        unlock_assistant: Callable[[], None] = lambda: None

        def request_assistant_unlock() -> None:
            unlock_assistant()

        with ui.tab_panels(tabs, value="configuration").classes("w-full bg-transparent pt-8"):
            with ui.tab_panel("configuration"):
                editor_refresh = configuration_editor(request_assistant_unlock)
            with ui.tab_panel("generator"):
                schedule_generator()
            with ui.tab_panel("viewer"):
                schedule_viewer()

        unlock_assistant = scheduler_ai_assistant(controller, editor_refresh)


def main() -> None:
    """Launch the NiceGUI application on the configured local port."""
    ui.run(
        root=build_app,
        title="MrLand Scheduler",
        reload=False,
        port=int(os.environ.get("MRLAND_GUI_PORT", "8080")),
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
