from src.services.lab_service import (
    add_lab_from_values,
    delete_lab_from_values,
    update_lab_from_values,
)


class LabController:
    """Coordinate lab CRUD for GUI views without leaking service details."""

    @staticmethod
    def add_lab(labs, name, capacity, features, times):
        return add_lab_from_values(labs, name, capacity, features, times)

    @staticmethod
    def update_lab(labs, existing_lab, name, capacity, features, times):
        return update_lab_from_values(labs, existing_lab, name, capacity, features, times)

    @staticmethod
    def delete_lab(labs, lab_to_delete):
        return delete_lab_from_values(labs, lab_to_delete)
