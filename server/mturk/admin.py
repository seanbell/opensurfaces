from django.contrib import admin

from mturk.models import Experiment, ExperimentSettings, PendingContent, \
    MtHitType, MtHitRequirement, MtHit, MtAssignment

admin.site.register(Experiment)
admin.site.register(ExperimentSettings)
admin.site.register(PendingContent)
admin.site.register(MtHitType)
admin.site.register(MtHitRequirement)


class MtHitAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['id', 'sandbox', 'hit_type', 'added']
        }),
        ('Status', {
            'fields': ['expired', 'hit_status', 'review_status']
        }),
        ('Assignments', {
            'fields': ['any_submitted_assignments', 'all_submitted_assignments',
                       'max_assignments', 'num_assignments_available',
                       'num_assignments_completed', 'num_assignments_pending']
        }),
        ('Views', {
            'fields': ['compatible_count', 'incompatible_count']
        }),
    ]

    # fields
    readonly_fields = ['added']
    list_display = ['hit_type', 'id', 'added', 'sandbox', 'expired', 'hit_status',
                    'review_status', 'max_assignments', 'num_assignments_available',
                    'any_submitted_assignments', 'all_submitted_assignments',
                    'compatible_count', 'incompatible_count']

    # field display
    list_filter = ['sandbox', 'expired', 'num_assignments_available',
                   'any_submitted_assignments', 'all_submitted_assignments',
                   'num_assignments_completed', 'num_assignments_pending']
    search_fields = ['hit_type__id', 'hit_type__description',
                     'hit_type__keywords', 'id']
    date_hierarchy = 'added'

admin.site.register(MtHit, MtHitAdmin)


class MtAssignmentAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': ['status', 'id', 'worker', 'hit',
                       'has_feedback', 'feedback', 'action_log',
                       'user_agent', 'post_meta', 'post_data']
        }),
        ('Date information', {
            'fields': ['added', 'accept_time', 'submit_time',
                       'approval_time', 'rejection_time', 'deadline',
                       'auto_approval_time'],
            #'classes': ['collapse']
        }),
    ]

    # fields
    readonly_fields = ['added']
    list_display = ['worker', 'hit', 'added', 'has_feedback', 'status']

    # field display
    list_filter = ['status', 'has_feedback', 'worker']
    search_fields = ['worker__mturk_worker_id', 'hit__id', 'id']
    date_hierarchy = 'added'

admin.site.register(MtAssignment, MtAssignmentAdmin)
