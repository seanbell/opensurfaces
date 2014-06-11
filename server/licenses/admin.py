from django.contrib import admin

from common.admin import AutoUserMixin
from licenses.models import License


class LicenseAdmin(AutoUserMixin, admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['added', 'name', 'url', 'creative_commons',
                        'cc_attribution', 'cc_noncommercial',
                       'cc_no_deriv', 'cc_share_alike']
        }),
    ]

    # fields
    readonly_fields = ['added']
    list_display = ['name', 'url']

    # field display
    list_filter = ['name', 'added']
    search_fields = ['name', 'url']


admin.site.register(License, LicenseAdmin)
