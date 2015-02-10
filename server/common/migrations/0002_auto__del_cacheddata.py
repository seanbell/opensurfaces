# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'CachedData'
        db.delete_table(u'common_cacheddata')


    def backwards(self, orm):
        # Adding model 'CachedData'
        db.create_table(u'common_cacheddata', (
            ('data', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=127, unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'common', ['CachedData'])


    models = {
        
    }

    complete_apps = ['common']