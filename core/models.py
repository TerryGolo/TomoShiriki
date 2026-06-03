from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from core.signals import booking_created, booking_status_changed

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

    def clean(self):
        super().clean()
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")
            
            if self.status in ['PENDING', 'APPROVED']:
                overlapping_bookings = Booking.objects.filter(
                    resource=self.resource,
                    status__in=['PENDING', 'APPROVED']
                ).filter(
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time
                )
                if self.pk:
                    overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
                
                if overlapping_bookings.exists():
                    raise ValidationError("The resource is already booked for this time frame.")

        if self.pk:
            try:
                db_instance = Booking.objects.get(pk=self.pk)
                old_status = db_instance.status
                if old_status != self.status:
                    allowed = {
                        'PENDING': ['APPROVED', 'REJECTED'],
                        'APPROVED': ['COMPLETED', 'CANCELLED'],
                    }
                    allowed_targets = allowed.get(old_status, [])
                    if self.status not in allowed_targets:
                        raise ValidationError(f"Invalid status transition from {old_status} to {self.status}.")
            except Booking.DoesNotExist:
                pass

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_status = None
        if not is_new:
            try:
                old_status = Booking.objects.get(pk=self.pk).status
            except Booking.DoesNotExist:
                pass
        
        self.clean()
        super().save(*args, **kwargs)
        
        if is_new:
            booking_created.send(sender=self.__class__, instance=self)
        elif old_status != self.status:
            booking_status_changed.send(
                sender=self.__class__, 
                instance=self, 
                old_status=old_status, 
                new_status=self.status
            )

    def __str__(self):
        return f"{self.resource.name} booked by {self.borrower.username}"
