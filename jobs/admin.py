from django.contrib import admin
from .models import JobPosting, JobApplication


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'location', 'job_type', 'salary_display', 'is_active', 'posted_at')
    list_filter = ('job_type', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'department', 'location', 'job_type', 'is_active')}),
        ('Compensation & Schedule', {'fields': ('salary_min', 'salary_max', 'salary_period', 'work_days', 'work_hours')}),
        ('Details', {'fields': ('description', 'requirements')}),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'status', 'submitted_at')
    list_filter = ('status', 'job')
    search_fields = ('full_name', 'email')
