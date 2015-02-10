# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("normals", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'ShapeName'
        db.create_table(u'shapes_shapename', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=127)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeName'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('representative_shape', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.MaterialShape'], null=True, blank=True)),
            ('fail', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'shapes', ['ShapeName'])

        # Adding model 'ShapeSubstance'
        db.create_table(u'shapes_shapesubstance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=127)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeSubstance'], null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('representative_shape', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.MaterialShape'], null=True, blank=True)),
            ('fail', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='substances', null=True, to=orm['shapes.ShapeSubstanceGroup'])),
        ))
        db.send_create_signal(u'shapes', ['ShapeSubstance'])

        # Adding model 'ShapeSubstanceGroup'
        db.create_table(u'shapes_shapesubstancegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'shapes', ['ShapeSubstanceGroup'])

        # Adding M2M table for field names on 'ShapeSubstanceGroup'
        m2m_table_name = db.shorten_name(u'shapes_shapesubstancegroup_names')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('shapesubstancegroup', models.ForeignKey(orm[u'shapes.shapesubstancegroup'], null=False)),
            ('shapename', models.ForeignKey(orm[u'shapes.shapename'], null=False))
        ))
        db.create_unique(m2m_table_name, ['shapesubstancegroup_id', 'shapename_id'])

        # Adding model 'MaterialShape'
        db.create_table(u'shapes_materialshape', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('vertices', self.gf('django.db.models.fields.TextField')()),
            ('num_vertices', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('triangles', self.gf('django.db.models.fields.TextField')()),
            ('num_triangles', self.gf('django.db.models.fields.IntegerField')()),
            ('segments', self.gf('django.db.models.fields.TextField')()),
            ('num_segments', self.gf('django.db.models.fields.IntegerField')()),
            ('area', self.gf('django.db.models.fields.FloatField')()),
            ('pixel_area', self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True)),
            ('special', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('special_slug', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('correct', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('correct_score', self.gf('django.db.models.fields.FloatField')(db_index=True, null=True, blank=True)),
            ('nice', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('nice_score', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('planar', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('planar_score', self.gf('django.db.models.fields.FloatField')(db_index=True, null=True, blank=True)),
            ('planar_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('image_crop', self.gf('django.db.models.fields.files.ImageField')(max_length=255, blank=True)),
            ('image_bbox', self.gf('django.db.models.fields.files.ImageField')(max_length=255, blank=True)),
            ('label_pos_x', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('label_pos_y', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('image_pbox', self.gf('django.db.models.fields.files.ImageField')(max_length=255, blank=True)),
            ('pbox_aspect_ratio', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('pbox', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('rectified_area', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dominant_r', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dominant_g', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dominant_b', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('dominant_rgb0', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True)),
            ('dominant_rgb1', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True)),
            ('dominant_rgb2', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True)),
            ('dominant_rgb3', self.gf('django.db.models.fields.CharField')(default='', max_length=7, blank=True)),
            ('dominant_delta', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('photo', self.gf('django.db.models.fields.related.ForeignKey')(related_name='material_shapes', to=orm['photos.Photo'])),
            ('substance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeSubstance'], null=True, blank=True)),
            ('substance_entropy', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('substance_score', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeName'], null=True, blank=True)),
            ('name_entropy', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('name_score', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('rectified_normal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['normals.ShapeRectifiedNormalLabel'], null=True, blank=True)),
            ('bsdf_wd', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bsdfs.ShapeBsdfLabel_wd'], null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['MaterialShape'])

        # Adding M2M table for field submitted_shapes on 'MaterialShape'
        m2m_table_name = db.shorten_name(u'shapes_materialshape_submitted_shapes')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('materialshape', models.ForeignKey(orm[u'shapes.materialshape'], null=False)),
            ('submittedshape', models.ForeignKey(orm[u'shapes.submittedshape'], null=False))
        ))
        db.create_unique(m2m_table_name, ['materialshape_id', 'submittedshape_id'])

        # Adding model 'SubmittedShape'
        db.create_table(u'shapes_submittedshape', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('photo', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submitted_shapes', to=orm['photos.Photo'])),
            ('vertices', self.gf('django.db.models.fields.TextField')(null=True)),
            ('num_vertices', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('shape_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal(u'shapes', ['SubmittedShape'])

        # Adding model 'ShapeSubstanceLabel'
        db.create_table(u'shapes_shapesubstancelabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('admin_score', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shape', self.gf('django.db.models.fields.related.ForeignKey')(related_name='substances', to=orm['shapes.MaterialShape'])),
            ('substance', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeSubstance'], null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['ShapeSubstanceLabel'])

        # Adding model 'MaterialShapeNameLabel'
        db.create_table(u'shapes_materialshapenamelabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('admin_score', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shape', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['shapes.MaterialShape'])),
            ('name', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shapes.ShapeName'], null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['MaterialShapeNameLabel'])

        # Adding model 'ShapePlanarityLabel'
        db.create_table(u'shapes_shapeplanaritylabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('admin_score', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shape', self.gf('django.db.models.fields.related.ForeignKey')(related_name='planarities', to=orm['shapes.MaterialShape'])),
            ('planar', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canttell', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['ShapePlanarityLabel'])

        # Adding model 'MaterialShapeQuality'
        db.create_table(u'shapes_materialshapequality', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('admin_score', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shape', self.gf('django.db.models.fields.related.ForeignKey')(related_name='qualities', to=orm['shapes.MaterialShape'])),
            ('correct', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canttell', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['MaterialShapeQuality'])

        # Adding model 'MaterialShapeNicenessLabel'
        db.create_table(u'shapes_materialshapenicenesslabel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('mturk_assignment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, on_delete=models.SET_NULL, to=orm['mturk.MtAssignment'])),
            ('sandbox', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('invalid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('quality_method', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('time_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('time_active_ms', self.gf('django.db.models.fields.IntegerField')(db_index=True, null=True, blank=True)),
            ('reward', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=8, decimal_places=4, blank=True)),
            ('admin_score', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('shape', self.gf('django.db.models.fields.related.ForeignKey')(related_name='nicenesses', to=orm['shapes.MaterialShape'])),
            ('nice', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('canttell', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'shapes', ['MaterialShapeNicenessLabel'])


    def backwards(self, orm):
        # Deleting model 'ShapeName'
        db.delete_table(u'shapes_shapename')

        # Deleting model 'ShapeSubstance'
        db.delete_table(u'shapes_shapesubstance')

        # Deleting model 'ShapeSubstanceGroup'
        db.delete_table(u'shapes_shapesubstancegroup')

        # Removing M2M table for field names on 'ShapeSubstanceGroup'
        db.delete_table(db.shorten_name(u'shapes_shapesubstancegroup_names'))

        # Deleting model 'MaterialShape'
        db.delete_table(u'shapes_materialshape')

        # Removing M2M table for field submitted_shapes on 'MaterialShape'
        db.delete_table(db.shorten_name(u'shapes_materialshape_submitted_shapes'))

        # Deleting model 'SubmittedShape'
        db.delete_table(u'shapes_submittedshape')

        # Deleting model 'ShapeSubstanceLabel'
        db.delete_table(u'shapes_shapesubstancelabel')

        # Deleting model 'MaterialShapeNameLabel'
        db.delete_table(u'shapes_materialshapenamelabel')

        # Deleting model 'ShapePlanarityLabel'
        db.delete_table(u'shapes_shapeplanaritylabel')

        # Deleting model 'MaterialShapeQuality'
        db.delete_table(u'shapes_materialshapequality')

        # Deleting model 'MaterialShapeNicenessLabel'
        db.delete_table(u'shapes_materialshapenicenesslabel')


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
        u'bsdfs.environmentmap': {
            'Meta': {'ordering': "['-id']", 'object_name': 'EnvironmentMap'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'tonemap_scale': ('django.db.models.fields.FloatField', [], {}),
            'tonemap_white': ('django.db.models.fields.FloatField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'bsdfs.shapebsdflabel_wd': {
            'Meta': {'ordering': "['-edit_nnz', '-time_ms']", 'object_name': 'ShapeBsdfLabel_wd'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'color': ('django.db.models.fields.CharField', [], {'max_length': '7'}),
            'color_L': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'color_a': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'color_b': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'color_correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'color_correct_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'contrast': ('django.db.models.fields.FloatField', [], {}),
            'doi': ('django.db.models.fields.IntegerField', [], {}),
            'edit_dict': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'edit_nnz': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'edit_sum': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'envmap': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bsdfs.EnvironmentMap']", 'null': 'True', 'blank': 'True'}),
            'give_up': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'give_up_msg': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gloss_correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'gloss_correct_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_blob': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'init_method': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'metallic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bsdfs_wd'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        u'normals.shaperectifiednormallabel': {
            'Meta': {'ordering': "['-admin_score']", 'object_name': 'ShapeRectifiedNormalLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'automatic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'canvas_height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'canvas_width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'correct_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'focal_pixels': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_rectified': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'num_vanishing_lines': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pos_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'pos_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rectified_normals'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'uvnb': ('django.db.models.fields.TextField', [], {})
        },
        u'photos.flickruser': {
            'Meta': {'ordering': "['-id']", 'object_name': 'FlickrUser'},
            'blacklisted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '127'})
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
            'rotated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scene_category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.PhotoSceneCategory']"}),
            'scene_category_correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'scene_category_correct_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'special': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stylized': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
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
        u'shapes.materialshape': {
            'Meta': {'ordering': "['-num_vertices', '-time_ms']", 'object_name': 'MaterialShape'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'area': ('django.db.models.fields.FloatField', [], {}),
            'bsdf_wd': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bsdfs.ShapeBsdfLabel_wd']", 'null': 'True', 'blank': 'True'}),
            'correct': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'correct_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'dominant_b': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'dominant_delta': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'dominant_g': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'dominant_r': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'dominant_rgb0': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '7', 'blank': 'True'}),
            'dominant_rgb1': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '7', 'blank': 'True'}),
            'dominant_rgb2': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '7', 'blank': 'True'}),
            'dominant_rgb3': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '7', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_bbox': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'image_crop': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'image_pbox': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'blank': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label_pos_x': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'label_pos_y': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeName']", 'null': 'True', 'blank': 'True'}),
            'name_entropy': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'name_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'nice': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'nice_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'num_segments': ('django.db.models.fields.IntegerField', [], {}),
            'num_triangles': ('django.db.models.fields.IntegerField', [], {}),
            'num_vertices': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'pbox': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pbox_aspect_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'material_shapes'", 'to': u"orm['photos.Photo']"}),
            'pixel_area': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'planar': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'planar_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'planar_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'rectified_area': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'rectified_normal': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['normals.ShapeRectifiedNormalLabel']", 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'segments': ('django.db.models.fields.TextField', [], {}),
            'special': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'special_slug': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'submitted_shapes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'material_shapes'", 'symmetrical': 'False', 'to': u"orm['shapes.SubmittedShape']"}),
            'substance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeSubstance']", 'null': 'True', 'blank': 'True'}),
            'substance_entropy': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'substance_score': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'triangles': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'vertices': ('django.db.models.fields.TextField', [], {})
        },
        u'shapes.materialshapenamelabel': {
            'Meta': {'ordering': "['-name', '-time_ms']", 'object_name': 'MaterialShapeNameLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'name': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeName']", 'null': 'True', 'blank': 'True'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'shapes.materialshapenicenesslabel': {
            'Meta': {'object_name': 'MaterialShapeNicenessLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'canttell': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'nice': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nicenesses'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'shapes.materialshapequality': {
            'Meta': {'object_name': 'MaterialShapeQuality'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'canttell': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'correct': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'qualities'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'shapes.shapename': {
            'Meta': {'ordering': "['-fail', 'name']", 'object_name': 'ShapeName'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeName']", 'null': 'True', 'blank': 'True'}),
            'representative_shape': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.MaterialShape']", 'null': 'True', 'blank': 'True'})
        },
        u'shapes.shapeplanaritylabel': {
            'Meta': {'object_name': 'ShapePlanarityLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'canttell': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'planar': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'planarities'", 'to': u"orm['shapes.MaterialShape']"}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'shapes.shapesubstance': {
            'Meta': {'ordering': "['-fail', 'name']", 'object_name': 'ShapeSubstance'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'fail': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'substances'", 'null': 'True', 'to': u"orm['shapes.ShapeSubstanceGroup']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeSubstance']", 'null': 'True', 'blank': 'True'}),
            'representative_shape': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.MaterialShape']", 'null': 'True', 'blank': 'True'})
        },
        u'shapes.shapesubstancegroup': {
            'Meta': {'ordering': "['-id']", 'object_name': 'ShapeSubstanceGroup'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'names': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'substance_groups'", 'symmetrical': 'False', 'to': u"orm['shapes.ShapeName']"})
        },
        u'shapes.shapesubstancelabel': {
            'Meta': {'ordering': "['-substance', '-time_ms']", 'object_name': 'ShapeSubstanceLabel'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'admin_score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'substances'", 'to': u"orm['shapes.MaterialShape']"}),
            'substance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shapes.ShapeSubstance']", 'null': 'True', 'blank': 'True'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'shapes.submittedshape': {
            'Meta': {'ordering': "['-time_ms']", 'object_name': 'SubmittedShape'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invalid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_assignment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['mturk.MtAssignment']"}),
            'num_vertices': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'photo': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submitted_shapes'", 'to': u"orm['photos.Photo']"}),
            'quality_method': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'reward': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '8', 'decimal_places': '4', 'blank': 'True'}),
            'sandbox': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'shape_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'time_active_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'time_ms': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"}),
            'vertices': ('django.db.models.fields.TextField', [], {'null': 'True'})
        }
    }

    complete_apps = ['shapes']
