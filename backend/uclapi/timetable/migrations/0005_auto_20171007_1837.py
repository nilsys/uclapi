# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-10-07 18:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetable', '0004_studentsa_studentsb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentsa',
            name='dob',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='studentsb',
            name='dob',
            field=models.DateField(blank=True, null=True),
        ),
    ]
