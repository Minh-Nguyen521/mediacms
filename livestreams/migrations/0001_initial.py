import livestreams.models
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
            name='LiveStream',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('stream_key', models.CharField(default=livestreams.models._generate_stream_key, max_length=64, unique=True)),
                ('status', models.CharField(
                    choices=[('offline', 'Offline'), ('live', 'Live'), ('ended', 'Ended')],
                    default='offline',
                    max_length=10,
                )),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('ended_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('creator', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='livestreams',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
