# Generated by Django 4.2 on 2023-04-19 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_review_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='created_at',
            field=models.DateTimeField(db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='photo',
            name='updated_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='created_at',
            field=models.DateTimeField(db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='review',
            name='updated_at',
            field=models.DateTimeField(null=True),
        ),
    ]
