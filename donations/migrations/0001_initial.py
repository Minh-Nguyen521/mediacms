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
            name='Donation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('donor_name', models.CharField(blank=True, max_length=150)),
                ('amount', models.PositiveIntegerField(help_text='Amount in VND')),
                ('message', models.TextField(blank=True, help_text='Optional message from donor to creator')),
                ('order_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('momo_trans_id', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
                    db_index=True, default='pending', max_length=20,
                )),
                ('raw_ipn', models.JSONField(default=dict)),
                ('payout_status', models.CharField(
                    choices=[('pending', 'Pending'), ('paid', 'Paid')],
                    db_index=True, default='pending', max_length=20,
                )),
                ('payout_note', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('creator', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='donations_received',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('donor', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='donations_sent',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
