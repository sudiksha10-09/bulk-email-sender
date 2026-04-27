# Generated migration for recipients app

import uuid
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecipientList',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('total_count', models.IntegerField(default=0)),
                ('valid_count', models.IntegerField(default=0)),
                ('invalid_count', models.IntegerField(default=0)),
                ('csv_file_url', models.URLField(max_length=500)),
                ('status', models.CharField(choices=[('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='processing', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipient_lists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Recipient List',
                'verbose_name_plural': 'Recipient Lists',
                'db_table': 'recipient_lists',
            },
        ),
        migrations.CreateModel(
            name='Recipient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=255)),
                ('metadata', models.JSONField(default=dict)),
                ('is_valid', models.BooleanField(default=True)),
                ('validation_error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('recipient_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipients', to='recipients.recipientlist')),
            ],
            options={
                'verbose_name': 'Recipient',
                'verbose_name_plural': 'Recipients',
                'db_table': 'recipients',
            },
        ),
        migrations.AddIndex(
            model_name='recipientlist',
            index=models.Index(fields=['user'], name='idx_reciplist_user'),
        ),
        migrations.AddIndex(
            model_name='recipient',
            index=models.Index(fields=['recipient_list'], name='idx_recip_list'),
        ),
        migrations.AddIndex(
            model_name='recipient',
            index=models.Index(fields=['email'], name='idx_recip_email'),
        ),
    ]
