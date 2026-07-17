from django.contrib import admin

from .models import MoMoTransaction, Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'rbac_group', 'is_active')
    list_filter = ('is_active',)


class MoMoTransactionInline(admin.TabularInline):
    model = MoMoTransaction
    extra = 0
    readonly_fields = ('order_id', 'amount', 'status', 'result_code', 'created_at')
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'momo_agreement_id')
    list_filter = ('status', 'plan')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [MoMoTransactionInline]
    actions = ['expire_selected']

    @admin.action(description='Expire selected subscriptions')
    def expire_selected(self, request, queryset):
        for sub in queryset.filter(status=Subscription.STATUS_ACTIVE):
            sub.expire()
        self.message_user(request, 'Selected subscriptions expired.')
