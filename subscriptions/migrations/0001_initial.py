from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('rbac', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('price', models.PositiveIntegerField(help_text='Price in VND')),
                ('duration_days', models.PositiveIntegerField(default=30)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this plan is offered to new subscribers')),
                ('rbac_group', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='rbac.rbacgroup',
                    help_text='RBAC group users are assigned to while this subscription is active',
                )),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('active', 'Active'), ('expired', 'Expired'), ('cancelled', 'Cancelled')],
                    db_index=True, default='pending', max_length=20,
                )),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, db_index=True, null=True)),
                ('momo_agreement_id', models.CharField(blank=True, db_index=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='subscriptions',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('plan', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    to='subscriptions.subscriptionplan',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='MoMoTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('request_id', models.CharField(max_length=255)),
                ('amount', models.PositiveIntegerField()),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('success', 'Success'), ('failed', 'Failed')],
                    default='pending', max_length=20,
                )),
                ('result_code', models.IntegerField(blank=True, null=True)),
                ('raw_response', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('subscription', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transactions',
                    to='subscriptions.subscription',
                )),
            ],
        ),
    ]
