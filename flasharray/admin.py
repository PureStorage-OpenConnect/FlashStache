"""Django Admin Configuration."""

from __future__ import unicode_literals

from django.contrib import admin
from flasharray.models import FlashArray


class QueueMixin(object):
    """Add Queues."""

    def get_form(self, request, obj=None, **kwargs):
        """Get the queues management form and add queues to it."""
        # pylint: disable=protected-access
        queue_field = self.model._meta.get_field('queue')
        queue_field.choices = [('default', 'default')]
        return super(QueueMixin, self).get_form(request, obj, **kwargs)


def toggle_disabled(modeladmin, request, queryset):
    """Add the action to enable one or more FlashArrays."""
    # pylint: disable=unused-argument
    queryset.update(enabled=False)
toggle_disabled.short_description = 'Disable monitoring for one or more FlashArrays'


def toggle_enabled(modeladmin, request, queryset):
    """Add the action to enable one or more FlashArrays."""
    # pylint: disable=unused-argument
    queryset.update(enabled=True)
toggle_enabled.short_description = 'Enable monitoring for one or more FlashArrays'


@admin.register(FlashArray)
class FlashArrayAdmin(QueueMixin, admin.ModelAdmin):
    """FlashArray Management Admin configuration for display."""
    actions = [toggle_disabled, toggle_enabled]
    list_display = ('hostname', 'enabled', 'date_added', 'retention_hours', 'interval')
    list_filter = ('hostname', 'enabled', 'retention_hours', 'interval')
    list_editable = ('enabled',)
    readonly_fields = ('job_id', 'date_added', 'queue', 'requests')
    fieldsets = (
        ('FlashArray', {'fields': ('hostname', 'ip_address', 'api_token', 'dashboards')}),
        ('Time Settings', {'fields': ('interval', 'retention_hours')}))
