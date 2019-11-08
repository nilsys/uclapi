# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-22 12:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0011_create_personal_timetable_function_1'),
    ]

    operations = [
        migrations.CreateModel(
            name='Stuclasses',
            fields=[
                ('setid', models.TextField(max_length=10)),
                ('studentid', models.TextField(max_length=12, primary_key=True, serialize=False)),
                ('courseid', models.TextField(max_length=12)),
                ('classgroupid', models.TextField(max_length=10)),
                ('clsgrpcode', models.TextField(max_length=10)),
                ('courseyear', models.BigIntegerField(blank=True, null=True)),
                ('fixingrp', models.CharField(blank=True, max_length=1, null=True)),
                ('inactive', models.CharField(blank=True, max_length=1, null=True)),
            ],
            options={
                'db_table': '"CMIS_OWNER"."STUCLASSES"',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='StuclassesA',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('setid', models.TextField(max_length=10)),
                ('studentid', models.TextField(max_length=12)),
                ('courseid', models.TextField(max_length=12)),
                ('classgroupid', models.TextField(max_length=10)),
                ('clsgrpcode', models.TextField(max_length=10)),
                ('courseyear', models.BigIntegerField(blank=True, null=True)),
                ('fixingrp', models.CharField(blank=True, max_length=1, null=True)),
                ('inactive', models.CharField(blank=True, max_length=1, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StuclassesB',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('setid', models.TextField(max_length=10)),
                ('studentid', models.TextField(max_length=12)),
                ('courseid', models.TextField(max_length=12)),
                ('classgroupid', models.TextField(max_length=10)),
                ('clsgrpcode', models.TextField(max_length=10)),
                ('courseyear', models.BigIntegerField(blank=True, null=True)),
                ('fixingrp', models.CharField(blank=True, max_length=1, null=True)),
                ('inactive', models.CharField(blank=True, max_length=1, null=True)),
            ],
        ),
    ]
