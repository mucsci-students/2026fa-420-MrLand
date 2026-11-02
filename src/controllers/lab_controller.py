# GUI controller for lab updates.

from src.controllers.lab_operations_controller import (
    add_lab_from_values,
    delete_lab_from_values,
    update_lab_from_values,
)


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
    def update_lab(labs, existing_lab, name, capacity, features, times):
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
        return update_lab_from_values(labs, existing_lab, name, capacity, features, times)

    @staticmethod
    def delete_lab(labs, lab_to_delete):
        """
        * Deletes a lab from a configuration.
        *
        * @param (labs) - List containing the lab being deleted
        * @param (lab_to_delete) - The lab being removed.
        *
        * Returns: The updated LabConfig
        """
        return delete_lab_from_values(labs, lab_to_delete)
