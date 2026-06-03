from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from core.models import Community, Resource, Booking

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with smart mock/dummy data for testing and demonstrations."

    def add_arguments(self, parser):
        parser.add_argument(
            '--scenario',
            type=str,
            default='basic',
            choices=['basic', 'workflow', 'overlap'],
            help='The scenario to load. Options: basic, workflow, overlap.'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing user, community, resource, and booking data before seeding.'
        )

    def handle(self, *args, **options):
        scenario = options['scenario']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            # Clear in dependency order
            Booking.objects.all().delete()
            Resource.objects.all().delete()
            Community.objects.all().delete()
            # Delete non-staff/non-superuser to retain local admin access
            User.objects.filter(is_superuser=False, is_staff=False).delete()
            self.stdout.write(self.style.SUCCESS("Existing data cleared successfully!"))

        self.stdout.write(self.style.NOTICE(f"Seeding scenario: '{scenario}'..."))

        try:
            with transaction.atomic():
                if scenario == 'basic':
                    self.seed_basic()
                elif scenario == 'workflow':
                    self.seed_workflow()
                elif scenario == 'overlap':
                    self.seed_overlap()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            raise CommandError(e)

    def get_or_create_users(self):
        # Create standard users
        admin, _ = User.objects.get_or_create(
            username='admin_user',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if _:
            admin.set_password('admin123')
            admin.save()

        alice, _ = User.objects.get_or_create(
            username='alice',
            defaults={'email': 'alice@example.com'}
        )
        if _:
            alice.set_password('password123')
            alice.save()

        bob, _ = User.objects.get_or_create(
            username='bob',
            defaults={'email': 'bob@example.com'}
        )
        if _:
            bob.set_password('password123')
            bob.save()

        charlie, _ = User.objects.get_or_create(
            username='charlie',
            defaults={'email': 'charlie@example.com'}
        )
        if _:
            charlie.set_password('password123')
            charlie.save()

        return admin, alice, bob, charlie

    def seed_basic(self):
        admin, alice, bob, charlie = self.get_or_create_users()

        # Create a community
        community, _ = Community.objects.get_or_create(
            name="Greenwood Community Share",
            defaults={'description': "A local sharing community for tools, gear, and more."}
        )
        community.members.add(alice, bob, charlie)

        # Create resources
        mower, _ = Resource.objects.get_or_create(
            name="Electric Lawnmower",
            owner_community=community,
            defaults={'description': "A high-efficiency cordless electric lawnmower."}
        )
        drill, _ = Resource.objects.get_or_create(
            name="Cordless Drill",
            owner_community=community,
            defaults={'description': "An 18V cordless drill with driver bits."}
        )
        truck, _ = Resource.objects.get_or_create(
            name="Alice's Cargo Trailer",
            owner_user=alice,
            defaults={'description': "A 10-foot enclosed cargo trailer."}
        )

        now = timezone.now()

        # Create some bookings
        # Booking 1: Pending booking by bob on Electric Lawnmower
        Booking.objects.create(
            resource=mower,
            borrower=bob,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=3),
            status='PENDING'
        )

        # Booking 2: Approved booking by bob on Cordless Drill
        Booking.objects.create(
            resource=drill,
            borrower=bob,
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=4),
            status='APPROVED'
        )

        # Booking 3: Pending booking by charlie on Alice's Cargo Trailer
        Booking.objects.create(
            resource=truck,
            borrower=charlie,
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=6),
            status='PENDING'
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded basic scenario!"))

    def seed_workflow(self):
        admin, alice, bob, charlie = self.get_or_create_users()

        # Create a community
        community, _ = Community.objects.get_or_create(
            name="Greenwood Community Share",
            defaults={'description': "A local sharing community for tools, gear, and more."}
        )
        community.members.add(alice, bob, charlie)

        # Create resources
        mower, _ = Resource.objects.get_or_create(
            name="Electric Lawnmower",
            owner_community=community,
            defaults={'description': "A high-efficiency cordless electric lawnmower."}
        )
        drill, _ = Resource.objects.get_or_create(
            name="Cordless Drill",
            owner_community=community,
            defaults={'description': "An 18V cordless drill with driver bits."}
        )
        truck, _ = Resource.objects.get_or_create(
            name="Alice's Cargo Trailer",
            owner_user=alice,
            defaults={'description': "A 10-foot enclosed cargo trailer."}
        )

        now = timezone.now()

        # Booking 1: PENDING
        Booking.objects.create(
            resource=mower,
            borrower=bob,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=2),
            status='PENDING'
        )

        # Booking 2: APPROVED
        Booking.objects.create(
            resource=drill,
            borrower=bob,
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=4),
            status='APPROVED'
        )

        # Booking 3: REJECTED
        Booking.objects.create(
            resource=mower,
            borrower=charlie,
            start_time=now + timedelta(days=1, hours=3),
            end_time=now + timedelta(days=1, hours=5),
            status='REJECTED'
        )

        # Booking 4: COMPLETED (starts in the past)
        Booking.objects.create(
            resource=truck,
            borrower=bob,
            start_time=now - timedelta(days=2, hours=4),
            end_time=now - timedelta(days=2),
            status='COMPLETED'
        )

        # Booking 5: CANCELLED
        Booking.objects.create(
            resource=drill,
            borrower=charlie,
            start_time=now + timedelta(days=3),
            end_time=now + timedelta(days=3, hours=2),
            status='CANCELLED'
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded workflow lifecycle scenario!"))

    def seed_overlap(self):
        admin, alice, bob, charlie = self.get_or_create_users()

        # Create a community
        community, _ = Community.objects.get_or_create(
            name="Greenwood Community Share",
            defaults={'description': "A local sharing community for tools, gear, and more."}
        )
        community.members.add(alice, bob, charlie)

        # Create resources
        mower, _ = Resource.objects.get_or_create(
            name="Electric Lawnmower",
            owner_community=community,
            defaults={'description': "A high-efficiency cordless electric lawnmower."}
        )

        now = timezone.now()

        # 1. Create an APPROVED booking
        Booking.objects.create(
            resource=mower,
            borrower=bob,
            start_time=now + timedelta(days=1),
            end_time=now + timedelta(days=1, hours=4),
            status='APPROVED'
        )

        # 2. Create a CANCELLED booking overlapping the APPROVED booking (Should succeed because CANCELLED)
        Booking.objects.create(
            resource=mower,
            borrower=alice,
            start_time=now + timedelta(days=1, hours=1),
            end_time=now + timedelta(days=1, hours=3),
            status='CANCELLED'
        )

        # 3. Create a REJECTED booking overlapping the APPROVED booking (Should succeed because REJECTED)
        Booking.objects.create(
            resource=mower,
            borrower=charlie,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=4),
            status='REJECTED'
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded overlap demo scenario!"))
        self.stdout.write(self.style.NOTICE("Attempting to create an overlapping PENDING booking to demonstrate validation rules..."))
        
        # 4. Demonstrate that a conflicting booking raises ValidationError
        conflicting_booking = Booking(
            resource=mower,
            borrower=charlie,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=3),
            status='PENDING'
        )
        try:
            conflicting_booking.clean()
            conflicting_booking.save()
            self.stdout.write(self.style.ERROR("Warning: Conflicting booking was unexpectedly saved without error!"))
        except ValidationError:
            self.stdout.write(self.style.SUCCESS("PASSED: Successfully blocked conflicting overlapping booking (ValidationError raised)."))
