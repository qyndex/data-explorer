"""Shared service singletons.

Import from here so all routers operate on the same in-memory state.
"""
from app.services.data_service import DataService

# Single shared instance — all routers import this object.
shared_data_service = DataService()
