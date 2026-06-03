from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError as DRFValidationError
from core.models import Community, Resource, Booking
from core.serializers import ResourceSerializer, BookingSerializer

User = get_user_model()

class ResourceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.community = Community.objects.create(name='Test Community')

    def test_resource_must_have_one_owner(self):
        # Resource without owner should raise ValidationError
        resource = Resource(name='No Owner Resource')
        with self.assertRaises(ValidationError):
            resource.save()

        # Resource with both owners should raise ValidationError
        resource2 = Resource(name='Two Owners Resource', owner_user=self.user, owner_community=self.community)
        with self.assertRaises(ValidationError):
            resource2.save()

        # Resource with user owner should be valid
        resource_user = Resource(name='User Resource', owner_user=self.user)
        resource_user.save()
        self.assertIsNotNone(resource_user.pk)

        # Resource with community owner should be valid
        resource_comm = Resource(name='Community Resource', owner_community=self.community)
        resource_comm.save()
        self.assertIsNotNone(resource_comm.pk)


class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.borrower = User.objects.create_user(username='borrower', password='password')
        self.resource = Resource.objects.create(name='Test Resource', owner_user=self.user)
        self.now = timezone.now()

    def test_booking_start_end_time(self):
        # start_time >= end_time should raise ValidationError
        booking = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now - timedelta(hours=1),
            status='PENDING'
        )
        with self.assertRaises(ValidationError):
            booking.save()

    def test_booking_overlap_validation(self):
        # Create an approved booking
        booking1 = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=2),
            status='APPROVED'
        )

        # Try to book overlapping slot (PENDING) -> should fail
        booking2 = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=3),
            status='PENDING'
        )
        with self.assertRaises(ValidationError):
            booking2.save()

        # Try to book overlapping slot (APPROVED) -> should fail
        booking3 = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now - timedelta(hours=1),
            end_time=self.now + timedelta(hours=1),
            status='APPROVED'
        )
        with self.assertRaises(ValidationError):
            booking3.save()

        # Non-overlapping booking (starts when booking1 ends) -> should succeed
        booking4 = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(hours=2),
            end_time=self.now + timedelta(hours=4),
            status='PENDING'
        )
        booking4.save()
        self.assertIsNotNone(booking4.pk)

        # Non-overlapping booking (ends when booking1 starts) -> should succeed
        booking5 = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now - timedelta(hours=2),
            end_time=self.now,
            status='PENDING'
        )
        booking5.save()
        self.assertIsNotNone(booking5.pk)

        # Cancelled booking shouldn't block new booking
        booking1.status = 'CANCELLED'
        booking1.save()

        booking6 = Booking(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(minutes=30),
            end_time=self.now + timedelta(hours=1),
            status='PENDING'
        )
        booking6.save()
        self.assertIsNotNone(booking6.pk)


class BookingSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.borrower = User.objects.create_user(username='borrower', password='password')
        self.resource = Resource.objects.create(name='Test Resource', owner_user=self.user)
        self.now = timezone.now()

    def test_serializer_overlap(self):
        # Create initial approved booking
        Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=2),
            status='APPROVED'
        )

        # Overlapping serializer data
        data = {
            'resource': self.resource.id,
            'borrower': self.borrower.id,
            'start_time': self.now + timedelta(hours=1),
            'end_time': self.now + timedelta(hours=3),
            'status': 'PENDING'
        }
        serializer = BookingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
