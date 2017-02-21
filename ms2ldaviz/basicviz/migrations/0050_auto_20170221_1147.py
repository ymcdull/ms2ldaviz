# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 11:47
from __future__ import unicode_literals

import basicviz.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('basicviz', '0049_auto_20170216_2228'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiment',
            name='csv_file',
            field=models.FileField(blank=True, null=True, upload_to=basicviz.models.get_upload_folder),
        ),
        migrations.AddField(
            model_name='experiment',
            name='mzml_file',
            field=models.FileField(null=True, upload_to=basicviz.models.get_upload_folder),
        ),
    ]
