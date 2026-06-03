from rest_framework import serializers
from .models import User, Community, Resource, Booking


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class CommunitySerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    member_ids = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True, source='members', required=False
    )

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'members', 'member_ids', 'created_at']
        read_only_fields = ['id', 'created_at']


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'name', 'description', 'owner_user', 'owner_community', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        owner_user = data.get('owner_user')
        owner_community = data.get('owner_community')
        if owner_user and owner_community:
            raise serializers.ValidationError(
                "A resource cannot belong to both a user and a community."
            )
        if not owner_user and not owner_community:
            raise serializers.ValidationError(
                "A resource must belong to either a user or a community."
            )
        return data


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['id', 'resource', 'borrower', 'start_time', 'end_time', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        instance = self.instance
        
        resource = data.get('resource', instance.resource if instance else None)
        start_time = data.get('start_time', instance.start_time if instance else None)
        end_time = data.get('end_time', instance.end_time if instance else None)
        status = data.get('status', instance.status if instance else 'PENDING')

        if not resource:
            raise serializers.ValidationError({"resource": "This field is required."})
        if not start_time:
            raise serializers.ValidationError({"start_time": "This field is required."})
        if not end_time:
            raise serializers.ValidationError({"end_time": "This field is required."})

        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")

        if status in ['PENDING', 'APPROVED']:
            overlapping_bookings = Booking.objects.filter(
                resource=resource,
                status__in=['PENDING', 'APPROVED']
            ).filter(
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if instance:
                overlapping_bookings = overlapping_bookings.exclude(pk=instance.pk)

            if overlapping_bookings.exists():
                raise serializers.ValidationError("The resource is already booked for this time frame.")

        if instance:
            old_status = instance.status
            if old_status != status:
                allowed = {
                    'PENDING': ['APPROVED', 'REJECTED'],
                    'APPROVED': ['COMPLETED', 'CANCELLED'],
                }
                allowed_targets = allowed.get(old_status, [])
                if status not in allowed_targets:
                    raise serializers.ValidationError(
                        {"status": f"Invalid status transition from {old_status} to {status}."}
                    )
                
                request = self.context.get('request')
                if request and hasattr(request, 'user'):
                    user = request.user
                    is_borrower = (user == instance.borrower)
                    is_owner = (instance.resource.owner_user == user)
                    is_admin = (user.is_staff or user.is_superuser)

                    if is_borrower:
                        if status != 'CANCELLED':
                            raise serializers.ValidationError(
                                {"status": "Borrowers can only transition their bookings to CANCELLED."}
                            )
                    elif is_owner or is_admin:
                        pass
                    else:
                        raise serializers.ValidationError(
                            {"status": "You do not have permission to change the status of this booking."}
                        )
        else:
            if status != 'PENDING':
                raise serializers.ValidationError(
                    {"status": "Initial status must be PENDING."}
                )

        return data
