"""
Custom User model and team/workspace support.

Why a custom User model from day one?
Django's built-in User is hard to extend after the first migration.
Starting with AUTH_USER_MODEL = "accounts.User" means you can add any
field you need later (avatar, preferences, API key) without painful migrations.
Best practice: always do this at the start of every Django project.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import UUIDModel


class User(AbstractUser):
    """
    Custom user model. Inherits all standard fields (username, email, password, etc.)
    and adds analytics-specific fields.

    We use email as the login identifier (configured in settings via allauth).
    """
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    bio = models.TextField(blank=True)

    # Preferences stored as JSON — flexible, avoids extra migrations for small settings
    preferences = models.JSONField(default=dict, blank=True)
    # e.g. {"default_chart_type": "bar", "theme": "light", "rows_per_page": 50}

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Workspace(UUIDModel):
    """
    A workspace groups analysts together — think of it as a team or organisation.
    Datasets belong to workspaces, not individual users, so analysts can collaborate.

    Example: "ACME Corp Analytics" workspace contains 50 datasets,
    accessible by the 8 analysts on that team.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT, related_name="owned_workspaces")
    members = models.ManyToManyField(
    User,
    through="WorkspaceMembership",
    through_fields=("workspace", "user"),
    related_name="workspaces",
)
    logo = models.ImageField(upload_to="workspace_logos/", null=True, blank=True)

    def __str__(self):
        return self.name


class WorkspaceMembership(UUIDModel):
    """
    Through model for Workspace ↔ User M2M relationship.
    Stores the role this user has within this workspace.
    Using a through model (instead of a simple ManyToManyField) lets us
    attach extra data (role) to the relationship itself.
    """
    class Role(models.TextChoices):
        VIEWER = "viewer", "Viewer"    # can view datasets and analyses, cannot modify
        EDITOR = "editor", "Editor"    # can upload data, create analyses and charts
        ADMIN  = "admin",  "Admin"     # can manage members, delete datasets, export all

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.VIEWER)
    invited_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="sent_invites")

    class Meta:
        unique_together = ("workspace", "user")  # one membership record per user per workspace
        verbose_name = "Workspace Membership"

    def __str__(self):
        return f"{self.user.email} → {self.workspace.name} ({self.role})"
