# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MtSubmittedContent'
        db.create_table(u'mturk_mtsubmittedcontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submitted_contents', to=orm['mturk.MtAssignment'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['MtSubmittedContent'])

        # Adding model 'ExperimentSettings'
        db.create_table(u'mturk_experimentsettings', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('auto_add_hits', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=4)),
            ('num_outputs_max', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('min_output_consensus', self.gf('django.db.models.fields.IntegerField')(default=4)),
            ('contents_per_hit', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('feedback_bonus', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='experiment_settings_in', to=orm['contenttypes.ContentType'])),
            ('out_content_type', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='experiment_settings_out', null=True, to=orm['contenttypes.ContentType'])),
            ('content_filter', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('out_content_attr', self.gf('django.db.models.fields.CharField')(max_length=127, blank=True)),
            ('out_count_ratio', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('frame_height', self.gf('django.db.models.fields.IntegerField')(default=800)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('duration', self.gf('django.db.models.fields.IntegerField')(default=1800)),
            ('lifetime', self.gf('django.db.models.fields.IntegerField')(default=2678400)),
            ('auto_approval_delay', self.gf('django.db.models.fields.IntegerField')(default=2592000)),
            ('max_active_hits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('max_total_hits', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('qualifications', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('requirements', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'mturk', ['ExperimentSettings'])

        # Adding model 'Experiment'
        db.create_table(u'mturk_experiment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('new_hit_settings', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='experiments', null=True, to=orm['mturk.ExperimentSettings'])),
            ('test_contents_per_assignment', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('variant', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('completed_id', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('version', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('has_tutorial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('template_dir', self.gf('django.db.models.fields.CharField')(default='mturk/experiments', max_length=255)),
            ('cubam_dirty', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('module', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('examples_group_attr', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal(u'mturk', ['Experiment'])

        # Adding unique constraint on 'Experiment', fields ['slug', 'variant']
        db.create_unique(u'mturk_experiment', ['slug', 'variant'])

        # Adding model 'PendingContent'
        db.create_table(u'mturk_pendingcontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='pending_contents', to=orm['mturk.Experiment'])),
            ('num_outputs_max', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('num_outputs_completed', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('num_outputs_scheduled', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('priority', self.gf('django.db.models.fields.FloatField')(default=0, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'mturk', ['PendingContent'])

        # Adding unique constraint on 'PendingContent', fields ['experiment', 'content_type', 'object_id']
        db.create_unique(u'mturk_pendingcontent', ['experiment_id', 'content_type_id', 'object_id'])

        # Adding M2M table for field hits on 'PendingContent'
        m2m_table_name = db.shorten_name(u'mturk_pendingcontent_hits')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pendingcontent', models.ForeignKey(orm[u'mturk.pendingcontent'], null=False)),
            ('mthit', models.ForeignKey(orm[u'mturk.mthit'], null=False))
        ))
        db.create_unique(m2m_table_name, ['pendingcontent_id', 'mthit_id'])

        # Adding model 'ExperimentExample'
        db.create_table(u'mturk_experimentexample', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='examples', to=orm['mturk.Experiment'])),
            ('good', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['ExperimentExample'])

        # Adding model 'ExperimentTestContent'
        db.create_table(u'mturk_experimenttestcontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='test_contents', to=orm['mturk.Experiment'])),
            ('priority', self.gf('django.db.models.fields.FloatField')(default=0, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['ExperimentTestContent'])

        # Adding model 'ExperimentTestContentResponse'
        db.create_table(u'mturk_experimenttestcontentresponse', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('test_content', self.gf('django.db.models.fields.related.ForeignKey')(related_name='responses', to=orm['mturk.ExperimentTestContent'])),
            ('experiment_worker', self.gf('django.db.models.fields.related.ForeignKey')(related_name='test_content_responses', to=orm['mturk.ExperimentWorker'])),
            ('assignment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='test_content_responses', to=orm['mturk.MtAssignment'])),
            ('correct', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('response', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'mturk', ['ExperimentTestContentResponse'])

        # Adding model 'ExperimentWorker'
        db.create_table(u'mturk_experimentworker', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='experiment_workers', to=orm['mturk.Experiment'])),
            ('worker', self.gf('django.db.models.fields.related.ForeignKey')(related_name='experiment_workers', to=orm['accounts.UserProfile'])),
            ('tutorial_completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('auto_approve', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('auto_approve_message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('blocked', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('blocked_reason', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('blocked_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('num_test_correct', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('num_test_incorrect', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'mturk', ['ExperimentWorker'])

        # Adding unique constraint on 'ExperimentWorker', fields ['experiment', 'worker']
        db.create_unique(u'mturk_experimentworker', ['experiment_id', 'worker_id'])

        # Adding model 'MtQualification'
        db.create_table(u'mturk_mtqualification', (
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=128, primary_key=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('auto_granted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('auto_granted_value', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('retry_delay', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
        ))
        db.send_create_signal(u'mturk', ['MtQualification'])

        # Adding model 'MtQualificationAssignment'
        db.create_table(u'mturk_mtqualificationassignment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('qualification', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['mturk.MtQualification'])),
            ('worker', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='qualifications', null=True, to=orm['accounts.UserProfile'])),
            ('value', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('granted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('num_correct', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_incorrect', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'mturk', ['MtQualificationAssignment'])

        # Adding model 'MtHitType'
        db.create_table(u'mturk_mthittype', (
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hit_types', to=orm['mturk.Experiment'])),
            ('experiment_settings', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hit_types', to=orm['mturk.ExperimentSettings'])),
            ('external_url', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('frame_height', self.gf('django.db.models.fields.IntegerField')(default=800)),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=128, primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(default='0.01', max_digits=8, decimal_places=4)),
            ('duration', self.gf('django.db.models.fields.IntegerField')(default=3600)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('auto_approval_delay', self.gf('django.db.models.fields.IntegerField')(default=2592000)),
            ('feedback_bonus', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=2, blank=True)),
        ))
        db.send_create_signal(u'mturk', ['MtHitType'])

        # Adding model 'MtHitQualification'
        db.create_table(u'mturk_mthitqualification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('hit_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='qualifications', to=orm['mturk.MtHitType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['MtHitQualification'])

        # Adding model 'MtHitRequirement'
        db.create_table(u'mturk_mthitrequirement', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('hit_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='requirements', to=orm['mturk.MtHitType'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['MtHitRequirement'])

        # Adding model 'MtHit'
        db.create_table(u'mturk_mthit', (
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=128, primary_key=True)),
            ('hit_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='hits', to=orm['mturk.MtHitType'])),
            ('lifetime', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('expired', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('any_submitted_assignments', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('all_submitted_assignments', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('max_assignments', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('num_assignments_available', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_assignments_completed', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_assignments_pending', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('incompatible_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('compatible_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('out_count_ratio', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('num_contents', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('hit_status', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('review_status', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'mturk', ['MtHit'])

        # Adding model 'MtHitContent'
        db.create_table(u'mturk_mthitcontent', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('hit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contents', to=orm['mturk.MtHit'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'mturk', ['MtHitContent'])

        # Adding model 'MtAssignment'
        db.create_table(u'mturk_mtassignment', (
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.CharField')(max_length=128, primary_key=True)),
            ('hit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='assignments', to=orm['mturk.MtHit'])),
            ('worker', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'], null=True, blank=True)),
            ('num_test_contents', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_test_correct', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('num_test_incorrect', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('accept_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('submit_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('approval_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('rejection_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deadline', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('auto_approval_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('has_feedback', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('feedback', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('feedback_bonus_given', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('bonus', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=2, blank=True)),
            ('bonus_message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('approve_message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('reject_message', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('action_log', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('partially_completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('user_agent', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('screen_width', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('screen_height', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('post_data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('post_meta', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('time_load_ms', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('wage', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('manually_rejected', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('submission_complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'mturk', ['MtAssignment'])

        # Adding M2M table for field test_contents on 'MtAssignment'
        m2m_table_name = db.shorten_name(u'mturk_mtassignment_test_contents')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('mtassignment', models.ForeignKey(orm[u'mturk.mtassignment'], null=False)),
            ('experimenttestcontent', models.ForeignKey(orm[u'mturk.experimenttestcontent'], null=False))
        ))
        db.create_unique(m2m_table_name, ['mtassignment_id', 'experimenttestcontent_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ExperimentWorker', fields ['experiment', 'worker']
        db.delete_unique(u'mturk_experimentworker', ['experiment_id', 'worker_id'])

        # Removing unique constraint on 'PendingContent', fields ['experiment', 'content_type', 'object_id']
        db.delete_unique(u'mturk_pendingcontent', ['experiment_id', 'content_type_id', 'object_id'])

        # Removing unique constraint on 'Experiment', fields ['slug', 'variant']
        db.delete_unique(u'mturk_experiment', ['slug', 'variant'])

        # Deleting model 'MtSubmittedContent'
        db.delete_table(u'mturk_mtsubmittedcontent')

        # Deleting model 'ExperimentSettings'
        db.delete_table(u'mturk_experimentsettings')

        # Deleting model 'Experiment'
        db.delete_table(u'mturk_experiment')

        # Deleting model 'PendingContent'
        db.delete_table(u'mturk_pendingcontent')

        # Removing M2M table for field hits on 'PendingContent'
        db.delete_table(db.shorten_name(u'mturk_pendingcontent_hits'))

        # Deleting model 'ExperimentExample'
        db.delete_table(u'mturk_experimentexample')

        # Deleting model 'ExperimentTestContent'
        db.delete_table(u'mturk_experimenttestcontent')

        # Deleting model 'ExperimentTestContentResponse'
        db.delete_table(u'mturk_experimenttestcontentresponse')

        # Deleting model 'ExperimentWorker'
        db.delete_table(u'mturk_experimentworker')

        # Deleting model 'MtQualification'
        db.delete_table(u'mturk_mtqualification')

        # Deleting model 'MtQualificationAssignment'
        db.delete_table(u'mturk_mtqualificationassignment')

        # Deleting model 'MtHitType'
        db.delete_table(u'mturk_mthittype')

        # Deleting model 'MtHitQualification'
        db.delete_table(u'mturk_mthitqualification')

        # Deleting model 'MtHitRequirement'
        db.delete_table(u'mturk_mthitrequirement')

        # Deleting model 'MtHit'
        db.delete_table(u'mturk_mthit')

        # Deleting model 'MtHitContent'
        db.delete_table(u'mturk_mthitcontent')

        # Deleting model 'MtAssignment'
        db.delete_table(u'mturk_mtassignment')

        # Removing M2M table for field test_contents on 'MtAssignment'
        db.delete_table(db.shorten_name(u'mturk_mtassignment_test_contents'))


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
        u'mturk.experimentexample': {
            'Meta': {'ordering': "['-id']", 'object_name': 'ExperimentExample'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'examples'", 'to': u"orm['mturk.Experiment']"}),
            'good': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
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
        u'mturk.experimenttestcontentresponse': {
            'Meta': {'ordering': "['-id']", 'object_name': 'ExperimentTestContentResponse'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'test_content_responses'", 'to': u"orm['mturk.MtAssignment']"}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'experiment_worker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'test_content_responses'", 'to': u"orm['mturk.ExperimentWorker']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response': ('django.db.models.fields.TextField', [], {}),
            'test_content': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': u"orm['mturk.ExperimentTestContent']"})
        },
        u'mturk.experimentworker': {
            'Meta': {'unique_together': "(('experiment', 'worker'),)", 'object_name': 'ExperimentWorker'},
            'auto_approve': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_approve_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blocked_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'blocked_reason': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'experiment_workers'", 'to': u"orm['mturk.Experiment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_test_correct': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_test_incorrect': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tutorial_completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'experiment_workers'", 'to': u"orm['accounts.UserProfile']"})
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
        u'mturk.mthitcontent': {
            'Meta': {'ordering': "['-id']", 'object_name': 'MtHitContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'hit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'contents'", 'to': u"orm['mturk.MtHit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'mturk.mthitqualification': {
            'Meta': {'object_name': 'MtHitQualification'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'hit_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'qualifications'", 'to': u"orm['mturk.MtHitType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        u'mturk.mthitrequirement': {
            'Meta': {'object_name': 'MtHitRequirement'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'hit_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'requirements'", 'to': u"orm['mturk.MtHitType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
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
        u'mturk.mtqualification': {
            'Meta': {'object_name': 'MtQualification'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'auto_granted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'auto_granted_value': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'primary_key': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'retry_delay': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'mturk.mtqualificationassignment': {
            'Meta': {'object_name': 'MtQualificationAssignment'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'granted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_correct': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'num_incorrect': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'qualification': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assignments'", 'to': u"orm['mturk.MtQualification']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'worker': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'qualifications'", 'null': 'True', 'to': u"orm['accounts.UserProfile']"})
        },
        u'mturk.mtsubmittedcontent': {
            'Meta': {'ordering': "['-id']", 'object_name': 'MtSubmittedContent'},
            'assignment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted_contents'", 'to': u"orm['mturk.MtAssignment']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'mturk.pendingcontent': {
            'Meta': {'unique_together': "(('experiment', 'content_type', 'object_id'),)", 'object_name': 'PendingContent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pending_contents'", 'to': u"orm['mturk.Experiment']"}),
            'hits': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'pending_contents'", 'symmetrical': 'False', 'to': u"orm['mturk.MtHit']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_outputs_completed': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'num_outputs_max': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_outputs_scheduled': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'priority': ('django.db.models.fields.FloatField', [], {'default': '0', 'db_index': 'True'})
        }
    }

    complete_apps = ['mturk']