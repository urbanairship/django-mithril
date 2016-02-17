# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Range',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField()),
                ('cidr', models.PositiveSmallIntegerField(default=32)),
            ],
        ),
        migrations.CreateModel(
            name='Whitelist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField()),
            ],
        ),
        migrations.AddField(
            model_name='range',
            name='whitelist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='mithril.Whitelist'),
        ),
        migrations.CreateModel(
            name='CachedWhitelist',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('mithril.whitelist',),
        ),
    ]
