from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Workspace, WorkspaceMembership


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "full_name", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(WorkspaceMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "workspace", "role"]
    list_filter = ["role"]
