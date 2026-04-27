# Generated migration for campaigns app

import uuid
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('recipients', '0001_initial'),
        ('smtp_config', '0001_initial'),
        ('templates', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('subject', models.CharField(max_length=500)),
                ('enable_ai_personalization', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('queued', 'Queued'), ('sending', 'Sending'), ('completed', 'Completed'), ('failed', 'Failed')], default='draft', max_length=20)),
                ('scheduled_at', models.DateTimeField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('total_recipients', models.IntegerField(default=0)),
                ('sent_count', models.IntegerField(default=0)),
                ('failed_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='campaigns', to='templates.template')),
                ('recipient_list', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='campaigns', to='recipients.recipientlist')),
                ('smtp_config', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='campaigns', to='smtp_config.smtpconfig')),
            ],
            options={
                'verbose_name': 'Campaign',
                'verbose_name_plural': 'Campaigns',
                'db_table': 'campaigns',
            },
        ),
        migrations.AddIndex(
            model_name='campaign',
            index=models.Index(fields=['user'], name='idx_campaign_user'),
        ),
        migrations.AddIndex(
            model_name='campaign',
            index=models.Index(fields=['status'], name='idx_campaign_status'),
        ),
    ]
