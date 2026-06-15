"""Shared enumerations."""

import enum


class UserRole(str, enum.Enum):
    """Whether the user is a student or a licensed practitioner."""

    medical_student = "medical_student"
    licensed_professional = "licensed_professional"
