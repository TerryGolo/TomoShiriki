from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Community, Resource, Booking

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Community)
admin.site.register(Resource)
admin.site.register(Booking)
