from django.conf import settings
from django.db import models


class Donation(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
    ]

    PAYOUT_PENDING = 'pending'
    PAYOUT_PAID = 'paid'
    PAYOUT_CHOICES = [
        (PAYOUT_PENDING, 'Pending'),
        (PAYOUT_PAID, 'Paid'),
    ]

    # The user who sent the donation. Stored even if they later delete their account.
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='donations_sent',
    )
    # Snapshot of the donor's display name at time of donation (survives account deletion).
    donor_name = models.CharField(max_length=150, blank=True)

    # The content creator receiving the donation.
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donations_received',
    )

    amount = models.PositiveIntegerField(help_text='Amount in VND')
    message = models.TextField(blank=True, help_text='Optional message from donor to creator')

    # MoMo order ID — unique identifier for this transaction.
    order_id = models.CharField(max_length=255, unique=True, db_index=True)
    momo_trans_id = models.CharField(max_length=255, blank=True, help_text='MoMo transaction ID from IPN')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    raw_ipn = models.JSONField(default=dict, help_text='Raw IPN payload from MoMo for audit')

    payout_status = models.CharField(max_length=20, choices=PAYOUT_CHOICES, default=PAYOUT_PENDING, db_index=True)
    payout_note = models.TextField(blank=True, help_text='Admin notes on manual payout (bank transfer reference etc.)')

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.donor_name or "Anonymous"} → {self.creator} | {self.amount:,} VND [{self.status}]'
