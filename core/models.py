from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class User(AbstractUser):
    pass

class Community(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='communities', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Communities"

class Resource(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Ownership: A resource can belong to an individual user OR a community.
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='owned_resources'
    )
    owner_community = models.ForeignKey(
        Community, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='owned_resources'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Enforce that exactly one owner is set
        if self.owner_user and self.owner_community:
            raise ValidationError("A resource cannot belong to both a user and a community directly.")
        if not self.owner_user and not self.owner_community:
            raise ValidationError("A resource must belong to either a user or a community.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrowed_items')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resource.name} booked by {self.borrower.username}"
