from django.contrib import admin

from imagekit.admin import AdminThumbnail
from common.admin import AutoUserMixin

from shapes.models import MaterialShape, SubmittedShape
from photos.models import FlickrUser, PhotoSceneCategory, Photo, \
    PhotoWhitebalanceLabel, PhotoSceneQualityLabel


admin.site.register(FlickrUser)
admin.site.register(PhotoSceneCategory)
admin.site.register(PhotoWhitebalanceLabel)
admin.site.register(PhotoSceneQualityLabel)


class PhotoAdmin(AutoUserMixin, admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['added', 'user', 'image_orig', 'admin_thumb_span6', 'aspect_ratio', 'scene_category',
                       'scene_category_correct', 'whitebalanced', 'description', 'exif',
                       'flickr_user', 'flickr_id']
        }),
    ]

    # fields
    readonly_fields = ['added', 'admin_thumb_span6']
    list_display = ['user', 'admin_thumb_span1', 'scene_category',
                    'scene_category_correct', 'whitebalanced', 'added']

    # field display
    list_filter = ['added', 'scene_category_correct', 'whitebalanced']
    search_fields = ['user', 'description']
    date_hierarchy = 'added'

    admin_thumb_span6 = AdminThumbnail(image_field='image_span6')
    admin_thumb_span1 = AdminThumbnail(image_field='thumb_span1')

    # inlines
    class PhotoLabelInlineBase(AutoUserMixin, admin.TabularInline):
        fk_name = 'photo'
        extra = 1

    class PhotoWhitebalanceLabelInline(PhotoLabelInlineBase):
        model = PhotoWhitebalanceLabel

    class PhotoSceneQualityLabelInline(PhotoLabelInlineBase):
        model = PhotoSceneQualityLabel

    class SubmittedShapeInline(PhotoLabelInlineBase):
        model = SubmittedShape

    class MaterialShapeInline(PhotoLabelInlineBase):
        model = MaterialShape

    inlines = [
        SubmittedShapeInline,
        MaterialShapeInline,
        PhotoWhitebalanceLabelInline,
        PhotoSceneQualityLabelInline,
    ]

admin.site.register(Photo, PhotoAdmin)


#class PhotoCollectionAdmin(AutoUserMixin, admin.ModelAdmin):
    #pass
#admin.site.register(PhotoCollection, PhotoCollectionAdmin)


#class PhotoSceneCategoryAdmin(AutoUserMixin, admin.ModelAdmin):
    #pass
#admin.site.register(PhotoSceneCategory, PhotoSceneCategoryAdmin)


#class PhotoAttributeAdmin(AutoUserMixin, admin.ModelAdmin):
    #pass
#admin.site.register(PhotoAttribute, PhotoAttributeAdmin)
