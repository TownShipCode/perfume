from __future__ import annotations

from enum import StrEnum


class State(StrEnum):
    IDLE = "idle"
    LANGUAGE_SELECTION = "language_selection"
    ORDERING = "ordering"
    ADDRESS_COLLECTION = "address_collection"
    ADDRESS_CONFIRMATION = "address_confirmation"
    POP_WAITING = "pop_waiting"
    CONFIRMED = "confirmed"
