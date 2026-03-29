"""
Global template context — injected into every template automatically.
Configured in settings.py TEMPLATES > context_processors.

Keeps views clean: they don't need to manually pass workspace/user data
to every template render call.
"""
def global_context(request):
    context = {}
    if request.user.is_authenticated:
        context["active_workspace"] = getattr(request.user, "active_workspace", None)
        context["dataset_count"] = 0  # will be filled once datasets app exists
    return context
