# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'License'
        db.create_table(u'licenses_license', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=255, blank=True)),
            ('creative_commons', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cc_attribution', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cc_noncommercial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cc_no_deriv', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('cc_share_alike', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('publishable', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'licenses', ['License'])


    def backwards(self, orm):
        # Deleting model 'License'
        db.delete_table(u'licenses_license')


    models = {
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
        }
    }

    complete_apps = ['licenses']