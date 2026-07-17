from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField(help_text='Price in VND')
    duration_days = models.PositiveIntegerField(default=30)
    # When a user activates this plan, they are added to this RBAC group as 'member'.
    # This is what gates access to premium content.
    rbac_group = models.ForeignKey(
        'rbac.RBACGroup',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='RBAC group users are assigned to while this subscription is active',
    )
    is_active = models.BooleanField(default=True, help_text='Whether this plan is offered to new subscribers')

    def __str__(self):
        return f'{self.name} ({self.price:,} VND / {self.duration_days} days)'


class Subscription(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True, db_index=True)
    # MoMo stores an agreementId after the first successful recurring payment.
    # This is used to initiate subsequent server-side charges.
    momo_agreement_id = models.CharField(max_length=255, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.plan.name} [{self.status}]'

    @property
    def is_active(self):
        return self.status == self.STATUS_ACTIVE and self.end_date and self.end_date > timezone.now()

    def activate(self):
        """Activate subscription and assign user to the plan's RBAC group."""
        from rbac.models import RBACMembership
        self.status = self.STATUS_ACTIVE
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        self.save(update_fields=['status', 'start_date', 'end_date', 'updated_at'])

        if self.plan.rbac_group:
            RBACMembership.objects.get_or_create(
                user=self.user,
                rbac_group=self.plan.rbac_group,
                defaults={'role': 'member'},
            )

    def expire(self):
        """Expire subscription and remove user from the plan's RBAC group."""
        from rbac.models import RBACMembership
        self.status = self.STATUS_EXPIRED
        self.save(update_fields=['status', 'updated_at'])

        if self.plan.rbac_group:
            # Only remove from group if the user has no other active subscription
            # that grants access to the same group.
            other_active = Subscription.objects.filter(
                user=self.user,
                plan__rbac_group=self.plan.rbac_group,
                status=self.STATUS_ACTIVE,
            ).exclude(pk=self.pk).exists()

            if not other_active:
                RBACMembership.objects.filter(
                    user=self.user,
                    rbac_group=self.plan.rbac_group,
                ).delete()


class MoMoTransaction(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='transactions')
    order_id = models.CharField(max_length=255, unique=True, db_index=True)
    request_id = models.CharField(max_length=255)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    result_code = models.IntegerField(null=True, blank=True)
    raw_response = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'MoMo {self.order_id} [{self.status}]'
