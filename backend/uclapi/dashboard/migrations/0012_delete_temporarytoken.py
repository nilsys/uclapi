# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-09 19:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_auto_20170930_1600'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TemporaryToken',
        ),
    ]
