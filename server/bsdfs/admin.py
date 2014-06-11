from django.contrib import admin

from common.admin import AutoUserMixin
from bsdfs.models import ShapeBsdfLabel_mf, ShapeBsdfLabel_wd


class ShapeBsdfLabelAdmin_wd(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeBsdfLabel_wd, ShapeBsdfLabelAdmin_wd)


class ShapeBsdfLabelAdmin_mf(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeBsdfLabel_mf, ShapeBsdfLabelAdmin_mf)
