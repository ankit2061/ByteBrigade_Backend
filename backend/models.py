

from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password

class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class User(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer-not-to-say', 'Prefer not to say'),
    ]

    # Authentication fields
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)

    # Profile fields
    name = models.CharField(max_length=100)
    college_name = models.CharField(max_length=100, null=True, blank=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True, null=True)

    # Skills
    my_skills = models.ManyToManyField(Skill, related_name="users", blank=True)

    # Social links
    linkedin_url = models.URLField(max_length=200, blank=True, null=True)
    github_url = models.URLField(max_length=200, blank=True, null=True)

    # Additional fields from frontend
    is_beginner = models.BooleanField(default=False)
    known_skills = models.ManyToManyField(Skill, related_name="known_by_users", blank=True)
    desired_skills = models.ManyToManyField(Skill, related_name="desired_by_users", blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username or self.name

    class Meta:
        ordering = ['-created_at']

#  HackathonExperience
class HackathonExperience(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hackathon_experiences')
    organizer_name = models.CharField(max_length=200)
    hackathon_name = models.CharField(max_length=200)
    description = models.TextField(max_length=1000, blank=True, null=True)
    achievements = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.hackathon_name} by {self.organizer_name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hackathon Experience'
        verbose_name_plural = 'Hackathon Experiences'
