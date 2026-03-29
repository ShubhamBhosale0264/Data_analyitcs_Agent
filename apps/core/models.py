"""
Base model classes that every other app inherits from.

Why a base model? Because every table in this project needs created_at,
updated_at, and a UUID primary key. Defining it once here means you never
forget to add these fields, and you can change the pattern in one place.
"""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base: adds created_at and updated_at to any model that inherits it.
    'abstract = True' means Django won't create a table for this — it only
    exists to be inherited.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]  # newest first everywhere by default


class UUIDModel(TimeStampedModel):
    """
    Extends TimeStampedModel with a UUID primary key.

    Why UUID instead of auto-increment integer?
    1. IDs don't leak information (user can't guess "there are 247 datasets")
    2. Safe to generate client-side before saving
    3. Works across distributed systems if you scale later
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
