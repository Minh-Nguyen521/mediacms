from django.contrib import admin
from django.db.models import Sum

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor_name', 'creator', 'amount', 'status', 'payout_status', 'created_at')
    list_filter = ('status', 'payout_status')
    search_fields = ('donor_name', 'creator__username', 'order_id', 'momo_trans_id')
    readonly_fields = ('donor', 'donor_name', 'creator', 'amount', 'order_id', 'momo_trans_id', 'status', 'raw_ipn', 'created_at', 'updated_at')
    fields = ('donor', 'donor_name', 'creator', 'amount', 'message', 'status', 'order_id', 'momo_trans_id', 'raw_ipn', 'payout_status', 'payout_note', 'created_at', 'updated_at')
    actions = ['mark_payout_paid']

    @admin.action(description='Mark selected donations as paid out')
    def mark_payout_paid(self, request, queryset):
        updated = queryset.filter(status=Donation.STATUS_SUCCESS, payout_status=Donation.PAYOUT_PENDING).update(
            payout_status=Donation.PAYOUT_PAID
        )
        self.message_user(request, f'{updated} donation(s) marked as paid out.')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('donor', 'creator')

    def changelist_view(self, request, extra_context=None):
        """Add payout summary totals to the changelist page."""
        extra_context = extra_context or {}
        qs = self.get_queryset(request).filter(status=Donation.STATUS_SUCCESS)
        extra_context['total_pending_payout'] = (
            qs.filter(payout_status=Donation.PAYOUT_PENDING).aggregate(t=Sum('amount'))['t'] or 0
        )
        return super().changelist_view(request, extra_context=extra_context)
