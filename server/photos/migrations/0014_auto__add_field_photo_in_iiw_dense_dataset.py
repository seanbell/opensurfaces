# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Photo.in_iiw_dense_dataset'
        db.add_column(u'photos_photo', 'in_iiw_dense_dataset',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        orm['photos.Photo'].objects.all() \
            .update(in_iiw_dense_dataset=False)

        dense_photo_ids = list(
            orm['intrinsic.IntrinsicPointComparison'].objects
            .filter(point1__min_separation__lt=0.05)
            .order_by('photo')
            .distinct('photo')
            .values_list('photo_id', flat=True)
        )

        if dense_photo_ids:
            orm['photos.Photo'].objects \
                .filter(in_iiw_dataset=True) \
                .filter(id__in=dense_photo_ids) \
                .update(in_iiw_dense_dataset=True)

    def backwards(self, orm):
        # Deleting field 'Photo.in_iiw_dense_dataset'
        db.delete_column(u'photos_photo', 'in_iiw_dense_dataset')


    models = {
        u'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'always_approve': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blocked_reason': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'exclude_from_aggregation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_worker_id': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['auth.User']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'intrinsic.intrinsicimagesalgorithm': {
            'Meta': {'unique_together': "(('slug', 'parameters'),)", 'object_name': 'IntrinsicImagesAlgorithm'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'baseline': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iiw_best': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'iiw_mean_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'parameters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'task_version': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'intrinsic.intrinsicimagesdecomposition': {
            'Meta': {'ordering': "['mean_error', '-id']", 'unique_together': "(('photo', 'algorithm'),)", 'object_name': 'IntrinsicImagesDecomposition'},
            'algorithm': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intrinsic_images_decompositions'", 'to': u"orm['intrinsic.IntrinsicImagesAlgorithm']"}),
            'error_comparison_thresh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mean_dense_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mean_eq_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mean_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mean_neq_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mean_sparse_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mean_sum_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'num': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_dense': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_eq': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_neq': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_sparse': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intrinsic_images_decompositions'", 'to': u"orm['photos.Photo']"}),
            'reflectance_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'runtime': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'shading_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'intrinsic.intrinsicpoint': {
            'Meta': {'ordering': "['-id']", 'object_name': 'IntrinsicPoint'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'min_separation': ('django.db.models.fields.DecimalField', [], {'default': "'0.07'", 'max_digits': '7', 'decimal_places': '5'}),
            'opaque': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'opaque_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'opaque_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intrinsic_points'", 'to': u"orm['photos.Photo']"}),
            'sRGB': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'synthetic_diff_cv': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'synthetic_diff_fraction': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'synthetic_diff_intensity': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'x': ('django.db.models.fields.FloatField', [], {}),
            'y': ('django.db.models.fields.FloatField', [], {})
        },
        u'intrinsic.intrinsicpointcomparison': {
            'Meta': {'ordering': "['photo', '-darker_score']", 'unique_together': "(('point1', 'point2'),)", 'object_name': 'IntrinsicPointComparison'},
            'darker': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'darker_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'darker_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'intrinsic_comparisons'", 'to': u"orm['photos.Photo']"}),
            'point1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comparison_point1'", 'to': u"orm['intrinsic.IntrinsicPoint']"}),
            'point1_image_darker': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'point2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comparison_point2'", 'to': u"orm['intrinsic.IntrinsicPoint']"}),
            'reflectance_dd': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'reflectance_dd_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'reflectance_eq': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'reflectance_eq_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'synthetic_diff_intensity_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'intrinsic.intrinsicpointcomparisonresponse': {
            'Meta': {'ordering': "['-time_ms']", 'object_name': 'IntrinsicPointComparisonResponse'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'comparison': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['intrinsic.IntrinsicPointComparison']"}),
            'confidence': ('django.db.models.fields.IntegerField', [], {}),
            'darker': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reflectance_dd': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'reflectance_eq': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'intrinsic.intrinsicpointopacityresponse': {
            'Meta': {'ordering': "['-time_ms']", 'object_name': 'IntrinsicPointOpacityResponse'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'opaque': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'opacities'", 'to': u"orm['intrinsic.IntrinsicPoint']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'zoom': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'intrinsic.intrinsicsyntheticdecomposition': {
            'Meta': {'ordering': "['-id']", 'object_name': 'IntrinsicSyntheticDecomposition'},
            'depth_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'diff_col_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'diff_dir_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'diff_ind_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'emit_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'env_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gloss_col_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gloss_dir_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'gloss_ind_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'md5': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
            'multilayer_exr': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'normal_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'intrinsic_synthetic'", 'unique': 'True', 'to': u"orm['photos.Photo']"}),
            'scene_artist': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'scene_url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'trans_col_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'trans_dir_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'trans_ind_thumb': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'licenses.license': {
            'Meta': {'object_name': 'License'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'cc_attribution': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_no_deriv': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_noncommercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_share_alike': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'creative_commons': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'publishable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'mturk.experiment': {
            'Meta': {'ordering': "['slug', 'variant']", 'unique_together': "(('slug', 'variant'),)", 'object_name': 'Experiment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'completed_id': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'cubam_dirty': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'examples_group_attr': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'has_tutorial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'module': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'new_hit_settings': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'experiments'", 'null': 'True', 'to': u"orm['mturk.ExperimentSettings']"}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'template_dir': ('django.db.models.fields.CharField', [], {'default': "'mturk/experiments'", 'max_length': '255'}),
            'test_contents_per_assignment': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'variant': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'mturk.experimentsettings': {
            'Meta': {'object_name': 'ExperimentSettings'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'auto_add_hits': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_approval_delay': ('django.db.models.fields.IntegerField', [], {'default': '2592000'}),
            'content_filter': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'experiment_settings_in'", 'to': u"orm['contenttypes.ContentType']"}),
            'contents_per_hit': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '1800'}),
            'feedback_bonus': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'frame_height': ('django.db.models.fields.IntegerField', [], {'default': '800'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'lifetime': ('django.db.models.fields.IntegerField', [], {'default': '2678400'}),
            'max_active_hits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'max_total_hits': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'min_output_consensus': ('django.db.models.fields.IntegerField', [], {'default': '4'}),
            'num_outputs_max': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'out_content_attr': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'out_content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'experiment_settings_out'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'out_count_ratio': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'qualifications': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'requirements': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'reward': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '4'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'mturk.experimenttestcontent': {
            'Meta': {'ordering': "['-id']", 'object_name': 'ExperimentTestContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'test_contents'", 'to': u"orm['mturk.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'priority': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'})
        },
        u'mturk.mtassignment': {
            'Meta': {'object_name': 'MtAssignment'},
            'accept_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'action_log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'approval_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'approve_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'auto_approval_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'bonus': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'bonus_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'feedback': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'feedback_bonus_given': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_feedback': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': u"orm['mturk.MtHit']"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'manually_rejected': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'num_test_contents': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_test_correct': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_test_incorrect': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'partially_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'post_data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'post_meta': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'reject_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'rejection_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'screen_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'screen_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'submission_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'submit_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_contents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'assignments'", 'symmetrical': 'False', 'to': u"orm['mturk.ExperimentTestContent']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time_load_ms': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user_agent': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'wage': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']", 'null': 'True', 'blank': 'True'})
        },
        u'mturk.mthit': {
            'Meta': {'object_name': 'MtHit'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'all_submitted_assignments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'any_submitted_assignments': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'compatible_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'expired': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hit_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'hit_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hits'", 'to': u"orm['mturk.MtHitType']"}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'incompatible_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'lifetime': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'max_assignments': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'num_assignments_available': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_assignments_completed': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_assignments_pending': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_contents': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'out_count_ratio': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'review_status': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'mturk.mthittype': {
            'Meta': {'object_name': 'MtHitType'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'auto_approval_delay': ('django.db.models.fields.IntegerField', [], {'default': '2592000'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '3600'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hit_types'", 'to': u"orm['mturk.Experiment']"}),
            'experiment_settings': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'hit_types'", 'to': u"orm['mturk.ExperimentSettings']"}),
            'external_url': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'feedback_bonus': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '2', 'blank': 'True'}),
            'frame_height': ('django.db.models.fields.IntegerField', [], {'default': '800'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'default': "'0.01'", 'max_digits': '8', 'decimal_places': '4'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'photos.flickruser': {
            'Meta': {'ordering': "['-id']", 'object_name': 'FlickrUser'},
            'blacklisted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sub_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'website_name': ('django.db.models.fields.CharField', [], {'max_length': '1023', 'blank': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '1023', 'blank': 'True'})
        },
        u'photos.photo': {
            'Meta': {'ordering': "['aspect_ratio', '-id']", 'object_name': 'Photo'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'aspect_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'exif': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'flickr_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'flickr_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.FlickrUser']"}),
            'focal_y': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'fov': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_orig': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'in_iiw_dataset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'in_iiw_dense_dataset': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'inappropriate': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['licenses.License']"}),
            'light_stack': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.PhotoLightStack']"}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'median_intrinsic_error': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'nonperspective': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'num_intrinsic_comparisons': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_intrinsic_points': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_shapes': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_vertices': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'orig_height': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'orig_width': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'rotated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scene_category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.PhotoSceneCategory']"}),
            'scene_category_correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scene_category_correct_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'scene_category_correct_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'stylized': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synthetic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'vanishing_length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'vanishing_lines': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'vanishing_points': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'whitebalanced': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'whitebalanced_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        u'photos.photolightstack': {
            'Meta': {'ordering': "['-id']", 'object_name': 'PhotoLightStack'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'photos.photoscenecategory': {
            'Meta': {'ordering': "['name']", 'object_name': 'PhotoSceneCategory'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['photos.PhotoSceneCategory']", 'null': 'True', 'blank': 'True'})
        },
        u'photos.photoscenequalitylabel': {
            'Meta': {'ordering': "['photo', '-time_ms']", 'object_name': 'PhotoSceneQualityLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'scene_qualities'", 'to': u"orm['photos.Photo']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'photos.photowhitebalancelabel': {
            'Meta': {'ordering': "['photo', '-time_ms']", 'object_name': 'PhotoWhitebalanceLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'chroma_median': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'num_points': ('django.db.models.fields.IntegerField', [], {}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'whitebalances'", 'to': u"orm['photos.Photo']"}),
            'points': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'whitebalanced': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['intrinsic', 'photos']
