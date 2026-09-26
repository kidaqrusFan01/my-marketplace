from django.contrib import admin
from .models import AgentProfile


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'user', 'created_at')
    search_fields = ('display_name', 'user__username', 'user__email')
