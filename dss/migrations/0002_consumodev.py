# Generated by Django 4.2.6 on 2023-10-25 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dss', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsumoDev',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kw_media_consumidos', models.FloatField()),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('duracion_m', models.IntegerField()),
            ],
        ),
    ]