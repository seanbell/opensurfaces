from django.contrib import admin

from common.admin import AutoUserMixin
from normals.models import ShapeRectifiedNormalLabel


class ShapeRectifiedNormalLabelAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeRectifiedNormalLabel, ShapeRectifiedNormalLabelAdmin)
