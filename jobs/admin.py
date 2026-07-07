from django.contrib import admin
from .models import JobPosting, JobApplication


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'location', 'job_type', 'is_active', 'posted_at')
    list_filter = ('job_type', 'is_active')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job', 'email', 'status', 'submitted_at')
    list_filter = ('status', 'job')
    search_fields = ('full_name', 'email')
