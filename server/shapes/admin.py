from django.contrib import admin

from imagekit.admin import AdminThumbnail

from common.admin import AutoUserMixin
from shapes.models import SubmittedShape, \
    MaterialShape, ShapeSubstance, ShapeSubstanceLabel, \
    ShapeName, MaterialShapeNameLabel, MaterialShapeQuality
from normals.models import ShapeRectifiedNormalLabel
from bsdfs.models import ShapeBsdfLabel_mf, ShapeBsdfLabel_wd


# inlines


class ShapeLabelInlineBase(AutoUserMixin, admin.TabularInline):
    extra = 1


class ShapeAdmin(AutoUserMixin, admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['added', 'photo', 'user', 'vertices', 'num_vertices']
        }),
    ]

    readonly_fields = ['added', 'admin_thumb_span6']
    list_display = ['user', 'admin_thumb_span1', 'added', 'num_vertices']
    list_filter = ['added', 'correct', 'planar']
    search_fields = ['user', 'photo']
    date_hierarchy = 'added'

    admin_thumb_span6 = AdminThumbnail(image_field='image_span6')
    admin_thumb_span1 = AdminThumbnail(image_field='thumb_span1')


class MaterialShapeAdmin(ShapeAdmin):

    class SubmittedShapeInline(ShapeLabelInlineBase):
        model = SubmittedShape

    class ShapeSubstanceLabelInline(ShapeLabelInlineBase):
        model = ShapeSubstanceLabel

    class ShapeBsdfLabelInline_mf(ShapeLabelInlineBase):
        model = ShapeBsdfLabel_mf

    class ShapeBsdfLabelInline_wd(ShapeLabelInlineBase):
        model = ShapeBsdfLabel_wd

    class ShapeRectifiedNormalLabelInline(ShapeLabelInlineBase):
        model = ShapeRectifiedNormalLabel

    inlines = [SubmittedShapeInline,
               ShapeSubstanceLabelInline,
               ShapeBsdfLabelInline_mf,
               ShapeBsdfLabelInline_wd,
               ShapeRectifiedNormalLabelInline]
admin.site.register(MaterialShape, MaterialShapeAdmin)


class SubmittedShapeAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(SubmittedShape, SubmittedShapeAdmin)


class ShapeNameAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeName, ShapeNameAdmin)


class MaterialShapeNameLabelAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(MaterialShapeNameLabel, MaterialShapeNameLabelAdmin)


class ShapeSubstanceAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeSubstance, ShapeSubstanceAdmin)


class ShapeSubstanceLabelAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(ShapeSubstanceLabel, ShapeSubstanceLabelAdmin)


class MaterialShapeQualityAdmin(AutoUserMixin, admin.ModelAdmin):
    pass
admin.site.register(MaterialShapeQuality, MaterialShapeQualityAdmin)
