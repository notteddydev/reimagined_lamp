# Generated by Django 4.2.13 on 2024-06-04 09:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address_book', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='user',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='contact',
            name='addresses',
            field=models.ManyToManyField(blank=True, to='address_book.address'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='dob',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='dod',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='family_members',
            field=models.ManyToManyField(blank=True, to='address_book.contact'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='met_through_contact',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='address_book.contact'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='nationality',
            field=models.ManyToManyField(blank=True, to='address_book.nation'),
        ),
        migrations.AlterField(
            model_name='contact',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]