# Generated migration for smtp_config app

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
            name='SMTPConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('provider', models.CharField(choices=[('gmail', 'Gmail'), ('sendgrid', 'SendGrid'), ('mailgun', 'Mailgun'), ('custom', 'Custom SMTP')], max_length=50)),
                ('host', models.CharField(max_length=255)),
                ('port', models.IntegerField()),
                ('username', models.CharField(max_length=255)),
                ('encrypted_password', models.BinaryField()),
                ('use_tls', models.BooleanField(default=True)),
                ('is_validated', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='smtp_configs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'SMTP Configuration',
                'verbose_name_plural': 'SMTP Configurations',
                'db_table': 'smtp_configs',
            },
        ),
        migrations.AddIndex(
            model_name='smtpconfig',
            index=models.Index(fields=['user'], name='idx_smtp_user'),
        ),
    ]
