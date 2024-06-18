# Generated by Django 4.2.13 on 2024-06-14 17:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('address_book', '0003_remove_contact_met_through_contact_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='mutual_contacts',
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='contact',
            name='tags',
            field=models.ManyToManyField(blank=True, to='address_book.tag'),
        ),
    ]