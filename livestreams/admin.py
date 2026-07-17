from django.contrib import admin

from .models import LiveStream


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'started_at', 'ended_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'creator__username', 'stream_key')
    readonly_fields = ('stream_key', 'started_at', 'ended_at', 'created_at')
    actions = ['force_offline']

    def force_offline(self, request, queryset):
        queryset.update(status=LiveStream.STATUS_OFFLINE)
        self.message_user(request, f'{queryset.count()} stream(s) set to offline.')
    force_offline.short_description = 'Force selected streams to offline'
