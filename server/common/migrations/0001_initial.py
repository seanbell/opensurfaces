# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CachedData'
        db.create_table(u'common_cacheddata', (
            ('key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=127, primary_key=True)),
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'common', ['CachedData'])


    def backwards(self, orm):
        # Deleting model 'CachedData'
        db.delete_table(u'common_cacheddata')


    models = {
        u'common.cacheddata': {
            'Meta': {'object_name': 'CachedData'},
            'data': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '127', 'primary_key': 'True'})
        }
    }

    complete_apps = ['common']