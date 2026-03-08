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
