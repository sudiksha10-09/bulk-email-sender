# Generated migration for tracking app

import uuid
import django.utils.timezone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('campaigns', '0001_initial'),
        ('recipients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tracking_id', models.UUIDField(db_index=True, default=uuid.uuid4, unique=True)),
                ('status', models.CharField(choices=[('sent', 'Sent'), ('failed', 'Failed'), ('bounced', 'Bounced')], max_length=20)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('retry_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_logs', to='campaigns.campaign')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_logs', to='recipients.recipient')),
            ],
            options={
                'verbose_name': 'Email Log',
                'verbose_name_plural': 'Email Logs',
                'db_table': 'email_logs',
            },
        ),
        migrations.CreateModel(
            name='EmailEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tracking_id', models.UUIDField(db_index=True)),
                ('event_type', models.CharField(choices=[('open', 'Open'), ('click', 'Click')], max_length=20)),
                ('event_data', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('email_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='tracking.emaillog')),
            ],
            options={
                'verbose_name': 'Email Event',
                'verbose_name_plural': 'Email Events',
                'db_table': 'email_events',
            },
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['campaign'], name='idx_emaillog_campaign'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['recipient'], name='idx_emaillog_recipient'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['tracking_id'], name='idx_emaillog_tracking'),
        ),
        migrations.AddIndex(
            model_name='emailevent',
            index=models.Index(fields=['email_log'], name='idx_event_emaillog'),
        ),
        migrations.AddIndex(
            model_name='emailevent',
            index=models.Index(fields=['tracking_id'], name='idx_event_tracking'),
        ),
        migrations.AddIndex(
            model_name='emailevent',
            index=models.Index(fields=['created_at'], name='idx_event_created'),
        ),
    ]
