# GUI controller for lab updates.

from src.controllers.lab_operations_controller import (
    add_lab_from_values,
    delete_lab_from_values,
    update_lab_from_values,
)
from src.models.configuration_observer import ConfigurationSubject, EntityChangeEvent


class LabController:
    @staticmethod
    def add_lab(labs, name, capacity, features, times):
        """
        * Adds a lab to a configuration that can be used by the scheduler
        *
        * @param (labs) - List of LabConfig objects
        * @param (name) - Lab Name
        * @param (capacity) - Max students per section
        * @param (features) - Equipment the course requires. Lab only valid if it has all of them.
        * @param (times) - Start time of the lab (None for unrestricted)
        *
        * Returns: The created LabConfig
        """
        return add_lab_from_values(labs, name, capacity, features, times)

    @staticmethod
    def update_lab(
        labs,
        existing_lab,
        name,
        capacity,
        features,
        times,
        change_subject: ConfigurationSubject | None = None,
    ):
        """
        * Updates a lab to a configuration. Overwrites previous value
        *
        * @param (labs) - List containing the lab being edited
        * @param (existing_lab) - The lab to modify
        * @param (name) - New lab name
        * @param (capacity) - New max students per section
        * @param (features) - New equipment the course requires. Lab only valid if it has all of them.
        * @param (times) - New start time of the lab (None for unrestricted)
        *
        * Returns: The updated LabConfig
        """
        old_name = existing_lab.name
        updated_lab = update_lab_from_values(
            labs, existing_lab, name, capacity, features, times
        )
        if updated_lab.name != old_name and change_subject is not None:
            change_subject.notify(
                EntityChangeEvent("lab", "renamed", old_name, updated_lab.name)
            )
        return updated_lab

    @staticmethod
    def delete_lab(
        labs,
        lab_to_delete,
        change_subject: ConfigurationSubject | None = None,
    ):
        """
        * Deletes a lab from a configuration.
        *
        * @param (labs) - List containing the lab being deleted
        * @param (lab_to_delete) - The lab being removed.
        *
        * Returns: The updated LabConfig
        """
        old_name = lab_to_delete.name
        deleted_lab = delete_lab_from_values(labs, lab_to_delete)
        if change_subject is not None:
            change_subject.notify(EntityChangeEvent("lab", "deleted", old_name))
        return deleted_lab
