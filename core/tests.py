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


from rest_framework.test import APIRequestFactory
from core.signals import booking_created, booking_status_changed

class BookingWorkflowTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='password')
        self.borrower = User.objects.create_user(username='borrower', password='password')
        self.resource = Resource.objects.create(name='Resource', owner_user=self.owner)
        self.now = timezone.now()

    def test_valid_transitions(self):
        # PENDING -> APPROVED
        booking = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=1),
            status='PENDING'
        )
        booking.status = 'APPROVED'
        booking.save()
        self.assertEqual(booking.status, 'APPROVED')

        # APPROVED -> COMPLETED
        booking.status = 'COMPLETED'
        booking.save()
        self.assertEqual(booking.status, 'COMPLETED')

        # Create another booking for PENDING -> REJECTED
        booking2 = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(hours=2),
            end_time=self.now + timedelta(hours=3),
            status='PENDING'
        )
        booking2.status = 'REJECTED'
        booking2.save()
        self.assertEqual(booking2.status, 'REJECTED')

        # Create another for APPROVED -> CANCELLED
        booking3 = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(hours=4),
            end_time=self.now + timedelta(hours=5),
            status='PENDING'
        )
        booking3.status = 'APPROVED'
        booking3.save()
        booking3.status = 'CANCELLED'
        booking3.save()
        self.assertEqual(booking3.status, 'CANCELLED')

    def test_invalid_transitions(self):
        # PENDING -> COMPLETED (invalid)
        booking = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=1),
            status='PENDING'
        )
        booking.status = 'COMPLETED'
        with self.assertRaises(ValidationError):
            booking.save()

        # REJECTED is terminal
        booking2 = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now + timedelta(hours=2),
            end_time=self.now + timedelta(hours=3),
            status='PENDING'
        )
        booking2.status = 'REJECTED'
        booking2.save()
        booking2.status = 'APPROVED'
        with self.assertRaises(ValidationError):
            booking2.save()


class BookingSerializerPermissionTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='password')
        self.borrower = User.objects.create_user(username='borrower', password='password')
        self.other_user = User.objects.create_user(username='other', password='password')
        self.admin_user = User.objects.create_user(username='admin', password='password', is_staff=True)
        self.resource = Resource.objects.create(name='Resource', owner_user=self.owner)
        self.now = timezone.now()
        self.factory = APIRequestFactory()

    def test_serializer_create_must_be_pending(self):
        # Try to create an APPROVED booking via serializer
        data = {
            'resource': self.resource.id,
            'borrower': self.borrower.id,
            'start_time': self.now,
            'end_time': self.now + timedelta(hours=1),
            'status': 'APPROVED'
        }
        serializer = BookingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)

    def test_borrower_can_only_cancel(self):
        # Start with an APPROVED booking
        booking = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=1),
            status='PENDING'
        )
        booking.status = 'APPROVED'
        booking.save()

        # Borrower wants to transition APPROVED -> CANCELLED (allowed)
        request = self.factory.patch('/')
        request.user = self.borrower
        serializer = BookingSerializer(
            instance=booking, 
            data={'status': 'CANCELLED'}, 
            partial=True, 
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())

        # Borrower wants to transition APPROVED -> COMPLETED (not allowed)
        serializer2 = BookingSerializer(
            instance=booking,
            data={'status': 'COMPLETED'},
            partial=True,
            context={'request': request}
        )
        self.assertFalse(serializer2.is_valid())
        self.assertIn('status', serializer2.errors)

    def test_owner_and_admin_permissions(self):
        # Start with PENDING booking
        booking = Booking.objects.create(
            resource=self.resource,
            borrower=self.borrower,
            start_time=self.now,
            end_time=self.now + timedelta(hours=1),
            status='PENDING'
        )

        # Owner wants to transition PENDING -> APPROVED (allowed)
        request = self.factory.patch('/')
        request.user = self.owner
        serializer = BookingSerializer(
            instance=booking,
            data={'status': 'APPROVED'},
            partial=True,
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())

        # Admin wants to transition PENDING -> APPROVED (allowed)
        request_admin = self.factory.patch('/')
        request_admin.user = self.admin_user
        serializer_admin = BookingSerializer(
            instance=booking,
            data={'status': 'APPROVED'},
            partial=True,
            context={'request': request_admin}
        )
        self.assertTrue(serializer_admin.is_valid())

        # Other user wants to transition PENDING -> APPROVED (not allowed)
        request_other = self.factory.patch('/')
        request_other.user = self.other_user
        serializer_other = BookingSerializer(
            instance=booking,
            data={'status': 'APPROVED'},
            partial=True,
            context={'request': request_other}
        )
        self.assertFalse(serializer_other.is_valid())
        self.assertIn('status', serializer_other.errors)


class BookingSignalsTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='password')
        self.borrower = User.objects.create_user(username='borrower', password='password')
        self.resource = Resource.objects.create(name='Resource', owner_user=self.owner)
        self.now = timezone.now()
        self.created_calls = []
        self.status_changed_calls = []

    def handle_created(self, sender, instance, **kwargs):
        self.created_calls.append((sender, instance))

    def handle_status_changed(self, sender, instance, old_status, new_status, **kwargs):
        self.status_changed_calls.append((sender, instance, old_status, new_status))

    def test_signals_fired(self):
        # Connect signals
        booking_created.connect(self.handle_created)
        booking_status_changed.connect(self.handle_status_changed)

        try:
            # Create a booking -> should trigger booking_created
            booking = Booking.objects.create(
                resource=self.resource,
                borrower=self.borrower,
                start_time=self.now,
                end_time=self.now + timedelta(hours=1),
                status='PENDING'
            )
            self.assertEqual(len(self.created_calls), 1)
            self.assertEqual(self.created_calls[0][0], Booking)
            self.assertEqual(self.created_calls[0][1], booking)
            self.assertEqual(len(self.status_changed_calls), 0)

            # Change status PENDING -> APPROVED -> should trigger booking_status_changed
            booking.status = 'APPROVED'
            booking.save()

            self.assertEqual(len(self.created_calls), 1)
            self.assertEqual(len(self.status_changed_calls), 1)
            self.assertEqual(self.status_changed_calls[0][0], Booking)
            self.assertEqual(self.status_changed_calls[0][1], booking)
            self.assertEqual(self.status_changed_calls[0][2], 'PENDING')
            self.assertEqual(self.status_changed_calls[0][3], 'APPROVED')
        finally:
            # Disconnect to clean up
            booking_created.disconnect(self.handle_created)
            booking_status_changed.disconnect(self.handle_status_changed)


from django.core.management import call_command

class SeederCommandTest(TestCase):
    def test_seed_basic_scenario(self):
        # Call command
        call_command('seed_data', '--scenario', 'basic', '--clear')
        
        # Verify users created
        self.assertTrue(User.objects.filter(username='alice').exists())
        self.assertTrue(User.objects.filter(username='bob').exists())
        self.assertTrue(User.objects.filter(username='charlie').exists())
        
        # Verify community created
        self.assertTrue(Community.objects.filter(name="Greenwood Community Share").exists())
        community = Community.objects.get(name="Greenwood Community Share")
        self.assertEqual(community.members.count(), 3)
        
        # Verify resources created
        self.assertEqual(Resource.objects.count(), 3)
        self.assertTrue(Resource.objects.filter(name="Electric Lawnmower").exists())
        
        # Verify bookings created
        self.assertEqual(Booking.objects.count(), 3)
        self.assertEqual(Booking.objects.filter(status='PENDING').count(), 2)
        self.assertEqual(Booking.objects.filter(status='APPROVED').count(), 1)

    def test_seed_workflow_scenario(self):
        call_command('seed_data', '--scenario', 'workflow', '--clear')
        
        # Verify bookings created in multiple statuses
        self.assertEqual(Booking.objects.count(), 5)
        self.assertTrue(Booking.objects.filter(status='PENDING').exists())
        self.assertTrue(Booking.objects.filter(status='APPROVED').exists())
        self.assertTrue(Booking.objects.filter(status='REJECTED').exists())
        self.assertTrue(Booking.objects.filter(status='COMPLETED').exists())
        self.assertTrue(Booking.objects.filter(status='CANCELLED').exists())

    def test_seed_overlap_scenario(self):
        call_command('seed_data', '--scenario', 'overlap', '--clear')
        
        # Verify overlap setup: 1 APPROVED, 1 CANCELLED, 1 REJECTED
        self.assertEqual(Booking.objects.count(), 3)
        mower = Resource.objects.get(name="Electric Lawnmower")
        
        approved_booking = Booking.objects.get(resource=mower, status='APPROVED')
        cancelled_booking = Booking.objects.get(resource=mower, status='CANCELLED')
        rejected_booking = Booking.objects.get(resource=mower, status='REJECTED')
        
        # Double check overlap exists in times
        self.assertTrue(cancelled_booking.start_time < approved_booking.end_time)
        self.assertTrue(cancelled_booking.end_time > approved_booking.start_time)

    def test_clear_flag(self):
        # Setup initial dummy data to check clearing
        user = User.objects.create_user(username='dummy', password='password')
        community = Community.objects.create(name='Dummy Community')
        resource = Resource.objects.create(name='Dummy Resource', owner_user=user)
        Booking.objects.create(
            resource=resource,
            borrower=user,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status='PENDING'
        )
        
        # Run seeder with clear flag
        call_command('seed_data', '--scenario', 'basic', '--clear')
        
        # Verify dummy data was deleted
        self.assertFalse(User.objects.filter(username='dummy').exists())
        self.assertFalse(Community.objects.filter(name='Dummy Community').exists())
        self.assertFalse(Resource.objects.filter(name='Dummy Resource').exists())

