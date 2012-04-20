# -*- coding: utf-8 -*-
# (c) 2012 Urban Airship and Contributors

import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Whitelist'
        db.create_table('mithril_whitelist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('mithril', ['Whitelist'])

        # Adding model 'Range'
        db.create_table('mithril_range', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('whitelist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mithril.Whitelist'])),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('cidr', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=32)),
        ))
        db.send_create_signal('mithril', ['Range'])

    def backwards(self, orm):
        # Deleting model 'Whitelist'
        db.delete_table('mithril_whitelist')

        # Deleting model 'Range'
        db.delete_table('mithril_range')

    models = {
        'mithril.range': {
            'Meta': {'object_name': 'Range'},
            'cidr': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'whitelist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['mithril.Whitelist']"})
        },
        'mithril.whitelist': {
            'Meta': {'object_name': 'Whitelist'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['mithril']
