from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import JobPosting
from .forms import JobApplicationForm


def job_list(request):
    jobs = JobPosting.objects.filter(is_active=True)
    job_type = request.GET.get('job_type', '')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    return render(request, 'jobs/list.html', {
        'jobs': jobs,
        'job_type_choices': JobPosting.JOB_TYPE_CHOICES,
        'selected_type': job_type,
    })


def job_detail(request, slug):
    job = get_object_or_404(JobPosting, slug=slug, is_active=True)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            if request.user.is_authenticated:
                application.applicant = request.user
            application.save()
            messages.success(request, "Your application was submitted successfully! We'll be in touch.")
            return redirect('jobs:job_detail', slug=slug)
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'full_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone_number': request.user.phone_number,
            }
        form = JobApplicationForm(initial=initial)

    return render(request, 'jobs/detail.html', {'job': job, 'form': form})
