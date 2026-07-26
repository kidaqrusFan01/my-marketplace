from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class JobPosting(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]
    SALARY_PERIOD_CHOICES = [
        ('year', 'Per Year'),
        ('month', 'Per Month'),
        ('week', 'Per Week'),
        ('hour', 'Per Hour'),
    ]

    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=150, default='Remote')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    description = models.TextField()
    requirements = models.TextField(blank=True)

    # Salary is a range (min/max) so postings can say "₦200,000 - ₦350,000
    # per month" without needing free-text formatting. Leave both blank for
    # "Salary not disclosed / negotiable".
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_period = models.CharField(max_length=10, choices=SALARY_PERIOD_CHOICES, default='month')

    work_days = models.CharField(
        max_length=100, blank=True, default='Monday - Friday',
        help_text="e.g. 'Monday - Friday' or 'Monday, Wednesday, Friday'"
    )
    work_hours = models.CharField(
        max_length=100, blank=True, default='9:00 AM - 5:00 PM',
        help_text="e.g. '9:00 AM - 5:00 PM' or '40 hours/week, flexible'"
    )

    is_active = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while JobPosting.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'slug': self.slug})

    @property
    def salary_display(self):
        """
        Human-readable salary string for templates, e.g.:
          '₦200,000 - ₦350,000 / Per Month'
          'From ₦150,000 / Per Month'
          'Up to ₦400,000 / Per Year'
          'Negotiable' (when neither min nor max is set)
        """
        period_label = self.get_salary_period_display()
        if self.salary_min and self.salary_max:
            return f"₦{self.salary_min:,.0f} - ₦{self.salary_max:,.0f} / {period_label}"
        if self.salary_min:
            return f"From ₦{self.salary_min:,.0f} / {period_label}"
        if self.salary_max:
            return f"Up to ₦{self.salary_max:,.0f} / {period_label}"
        return "Negotiable"

    def __str__(self):
        return self.title


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('interview', 'Interview'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_applications'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} -> {self.job.title}"
