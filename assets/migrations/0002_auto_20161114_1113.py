# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-14 03:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='manufactory',
            old_name='manufactory',
            new_name='name',
        ),
    ]