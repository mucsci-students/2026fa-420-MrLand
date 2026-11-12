
"""What-If Analysis tab."""

from nicegui import ui

from src.views.schedule_analysis.analysis_components import (
    placeholder,
    surface_card,
)


def build_what_if_tab() -> None:
    """Build the What-If Analysis tab layout."""

    # ---------------------------------------------------------
    # Custom styling
    # ---------------------------------------------------------

    ui.add_head_html("""
        <style>
            .what-if-page {
                color: var(--app-foreground);
            }

            .what-if-tabs {
                background: transparent;
                color: var(--text-muted);
            }

            .what-if-tabs .q-tab {
                color: var(--text-muted);
                font-weight: 500;
                min-height: 42px;
            }

            .what-if-tabs .q-tab--active {
                color: var(--text-primary);
            }

            .what-if-tabs .q-tab__indicator {
                background: var(--accent-color);
                height: 2px;
            }

            .what-if-dialog {
                background: var(--surface);
                color: var(--app-foreground);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                min-width: 480px;
                max-width: 90vw;
            }

            .what-if-dialog .q-field__control {
                background: var(--surface-raised);
            }
        </style>
    """)

    # ---------------------------------------------------------
    # Generation options
    # ---------------------------------------------------------

    optimizer_flags = {
        "Faculty Course Preferences": "faculty_course",
        "Faculty Room Preferences": "faculty_room",
        "Faculty Lab Preferences": "faculty_lab",
        "Same Room": "same_room",
        "Same Lab": "same_lab",
        "Pack Rooms": "pack_rooms",
        "Pack Labs": "pack_labs",
    }

    # ---------------------------------------------------------
    # Dialog behaviors
    # ---------------------------------------------------------

    def update_optimizer_override_state(enabled: bool) -> None:
        """Enable or disable temporary optimizer options."""
        for checkbox in temporary_optimizer_checkboxes.values():
            if enabled:
                checkbox.enable()
            else:
                checkbox.disable()

    def confirm_generation() -> None:
        """Placeholder for the future schedule generation workflow."""
        generation_dialog.close()
        ui.notify(
            "Schedule generation will be connected during implementation.",
            type="info",
        )

    # ---------------------------------------------------------
    # Generation options dialog
    # ---------------------------------------------------------

    with (
        ui.dialog() as generation_dialog,
        ui.card().classes("what-if-dialog w-full gap-4 p-5"),
    ):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Generate Schedules").classes(
                "text-xl font-semibold"
            ).style("color: var(--text-primary)")

            ui.button(
                icon="close",
                on_click=generation_dialog.close,
            ).props("flat round dense").style(
                "color: var(--text-muted)"
            )

        ui.label(
            "Configure the generation options for this experiment."
        ).classes("text-sm").style("color: var(--text-muted)")

        # Generation limit
        with ui.column().classes("w-full gap-2"):
            ui.label("Generation Limit").classes(
                "font-semibold"
            ).style("color: var(--text-primary)")

            generation_limit = (
                ui.input(
                    label="Maximum schedules",
                    placeholder="Use configured limit",
                )
                .props("outlined type=number")
                .classes("w-full")
            )

            ui.label(
                "Leave blank to use the limit configured in the base configuration."
            ).classes("text-xs").style("color: var(--text-muted)")

        ui.separator().style("background: var(--border-color)")

        # Time slot overrides
        with ui.column().classes("w-full gap-3"):
            ui.label("Time Slot Settings").classes(
                "font-semibold"
            ).style("color: var(--text-primary)")

            max_time_gap_override = (
                ui.input(
                    label="Maximum Time Gap Override (minutes)",
                    placeholder="Use configured value",
                )
                .props("outlined type=number")
                .classes("w-full")
            )

            min_time_overlap_override = (
                ui.input(
                    label="Minimum Time Overlap Override (minutes)",
                    placeholder="Use configured value",
                )
                .props("outlined type=number")
                .classes("w-full")
            )

        ui.separator().style("background: var(--border-color)")

        # Optimizer options
        with ui.column().classes("w-full gap-2"):
            ui.label("Optimizer Options").classes(
                "font-semibold"
            ).style("color: var(--text-primary)")

            ui.label(
                "Optionally replace the configured optimizer options "
                "for this generation."
            ).classes("text-xs").style("color: var(--text-muted)")

            optimizer_override_enabled = ui.checkbox(
                "Use temporary optimizer overrides"
            )

            temporary_optimizer_checkboxes = {}

            with ui.column().classes("w-full gap-1 pl-2"):
                for label, value in optimizer_flags.items():
                    temporary_optimizer_checkboxes[value] = ui.checkbox(
                        label
                    )

            for checkbox in temporary_optimizer_checkboxes.values():
                checkbox.disable()

            optimizer_override_enabled.on_value_change(
                update_optimizer_override_state
            )

        ui.separator().style("background: var(--border-color)")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(
                "Cancel",
                on_click=generation_dialog.close,
            ).props("flat").style("color: var(--text-muted)")

            ui.button(
                "Generate Schedules",
                icon="auto_awesome",
                on_click=confirm_generation,
            ).props("unelevated color=primary")

    # ---------------------------------------------------------
    # Main page
    # ---------------------------------------------------------

    with ui.column().classes("what-if-page w-full gap-4"):

        # -----------------------------------------------------
        # Base configuration selector
        # -----------------------------------------------------

        with ui.row().classes(
            "w-full items-center justify-between gap-4 flex-wrap"
        ):
            with ui.column().classes("gap-1"):
                ui.label("Base Configuration").classes(
                    "text-xs font-semibold tracking-wide"
                ).style("color: var(--text-muted)")

                ui.label("Select a configuration to experiment with.").classes(
                    "text-sm"
                ).style("color: var(--text-muted)")

        with ui.row().classes(
            "w-full items-center justify-between gap-4 flex-wrap"
        ):
            base_config_select = (
                ui.select(
                    options={},
                    label="Base Configuration",
                    value=None,
                )
                .props("outlined clearable")
                .classes("w-full max-w-md")
            )

            ui.button(
                "Load Configuration",
                icon="folder_open",
            ).props("outline").classes("h-14 px-5")

        # -----------------------------------------------------
        # Editor and Results navigation
        # -----------------------------------------------------

        with ui.row().classes("w-full items-center justify-between"):
            with ui.tabs().props("dense no-caps").classes(
                "what-if-tabs"
            ) as what_if_tabs:
                ui.tab("editor", label="Editor")
                ui.tab("results", label="Results")

        with ui.tab_panels(
            what_if_tabs,
            value="editor",
        ).classes("w-full"):

            # =================================================
            # EDITOR TAB
            # =================================================

            with ui.tab_panel("editor"):
                with ui.column().classes("w-full gap-4"):
                        
                    # Editor heading and toolbar
                    with ui.row().classes(
                        "w-full items-center justify-between gap-3 flex-wrap"
                    ):
                        
                        with ui.column().classes("gap-1"):
                            ui.label("Configuration Editor").classes(
                                "text-xl font-semibold"
                            ).style("color: var(--text-primary)")

                            ui.label(
                                "Modify a temporary copy of your configuration."
                            ).classes("text-sm").style(
                                "color: var(--text-muted)"
                            )
                        
                        ui.space()

                        # Generate button
                        ui.button(
                            "Generate",
                            icon="auto_awesome",
                            on_click=generation_dialog.open,
                        ).props("unelevated")


                    # Change summary
                    with ui.expansion(
                        "Change Summary",
                        icon="difference",
                    ).classes("w-full").style(
                        "background: var(--surface); "
                        "border: 1px solid var(--border-color); "
                        "border-radius: 12px; "
                        "color: var(--text-primary);"
                    ):
                        with ui.column().classes("w-full gap-2 p-2"):
                            placeholder(
                                "Changes to the base configuration "
                                "will be summarized here."
                            )

                    # Main editor workspace
                    with surface_card(
                        "Configuration Workspace",
                        "Select a configuration category to begin editing.",
                    ):
                        with ui.column().classes(
                            "w-full min-h-[350px] items-center justify-center gap-3"
                        ):
                            ui.icon(
                                "settings",
                                size="42px",
                            ).style("color: var(--text-muted)")

                            ui.label(
                                "Configuration editor will appear here."
                            ).classes("text-base font-semibold").style(
                                "color: var(--text-primary)"
                            )

                            placeholder(
                                "The existing configuration editor "
                                "will be integrated here."
                            )

            # =================================================
            # RESULTS TAB
            # =================================================

            with ui.tab_panel("results"):
                with ui.column().classes("w-full gap-4"):

                    # Results heading
                    with ui.row().classes(
                        "w-full items-center justify-between gap-3 flex-wrap"
                    ):
                        with ui.column().classes("gap-1"):
                            ui.label("Generated Results").classes(
                                "text-xl font-semibold"
                            ).style("color: var(--text-primary)")

                            ui.label(
                                "Review and compare alternative schedules."
                            ).classes("text-sm").style(
                                "color: var(--text-muted)"
                            )

                    # Results summary
                    with surface_card(
                        "Generation Summary",
                        "Overview of the schedules generated for this experiment.",
                    ):
                        placeholder(
                            "Generated count, valid schedules, "
                            "and generation warnings will appear here."
                        )

                    # Schedule selection
                    with surface_card(
                        "Schedule Preview",
                        "Select an alternative to review its schedule.",
                    ):
                        with ui.row().classes(
                            "w-full items-center justify-between gap-3 flex-wrap"
                        ):
                            ui.select(
                                options={},
                                label="Generated Schedule",
                            ).props("outlined").classes("w-full max-w-sm")

                            ui.button(
                                "Compare",
                                icon="compare_arrows",
                            ).props("outline")

                        with ui.column().classes(
                            "w-full min-h-[350px] items-center justify-center gap-3"
                        ):
                            ui.icon(
                                "calendar_month",
                                size="42px",
                            ).style("color: var(--text-muted)")

                            ui.label(
                                "Schedule preview will appear here."
                            ).classes("text-base font-semibold").style(
                                "color: var(--text-primary)"
                            )

                            placeholder(
                                "The existing Schedule Viewer will be integrated here."
                            )
