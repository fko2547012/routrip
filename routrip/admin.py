from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Log, Spot, Logcard, Section, Tag


class LogcardInline(admin.TabularInline):
    model = Logcard
    extra = 0


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'display_name', 'is_public', 'is_staff')
    search_fields = ('username', 'display_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('プロフィール', {'fields': ('display_name', 'is_public')}),
        ('権限', {'fields': ('is_active', 'is_staff', 'is_superuser',
                            'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',),
                'fields': ('username', 'display_name', 'password1', 'password2')}),
    )


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start_spot', 'trip_start_date',
                    'trip_end_date', 'posted_at')
    list_filter = ('trip_start_date', 'user')
    search_fields = ('title',)
    filter_horizontal = ('tags',)
    inlines = [LogcardInline, SectionInline]


@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude', 'registered_user')
    search_fields = ('name',)


@admin.register(Logcard)
class LogcardAdmin(admin.ModelAdmin):
    list_display = ('id', 'log', 'spot', 'display_order', 'taken_at')
    list_filter = ('log',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'log', 'from_spot', 'to_spot', 'section_order',
                    'transport', 'duration')
    list_filter = ('log',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)