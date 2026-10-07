from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Log, Spot, Logcard, section, tag

admin.site.register(User, UserAdmin)
admin.site.register(Log)
admin.site.register(Spot)
admin.site.register(Logcard)
admin.site.register(section)
admin.site.register(tag)