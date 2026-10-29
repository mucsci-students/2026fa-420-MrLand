from nicegui.client import Client
from nicegui.testing.user import User


def active_client(user: User) -> Client:
    client = user.client
    assert client is not None
    return client
