from django.apps import AppConfig


class SmtpConfigConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.smtp_config'
    verbose_name = 'SMTP Configuration'
