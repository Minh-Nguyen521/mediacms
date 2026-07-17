import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def _generate_stream_key():
    return secrets.token_hex(16)


class LiveStream(models.Model):
    STATUS_OFFLINE = 'offline'
    STATUS_LIVE = 'live'
    STATUS_ENDED = 'ended'
    STATUS_CHOICES = [
        (STATUS_OFFLINE, 'Offline'),
        (STATUS_LIVE, 'Live'),
        (STATUS_ENDED, 'Ended'),
    ]

    title = models.CharField(max_length=255)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='livestreams',
    )
    stream_key = models.CharField(max_length=64, unique=True, default=_generate_stream_key)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_OFFLINE)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_status_display()}) — {self.creator}'

    def go_live(self):
        self.status = self.STATUS_LIVE
        self.started_at = timezone.now()
        self.ended_at = None
        self.save(update_fields=['status', 'started_at', 'ended_at'])

    def end_stream(self):
        self.status = self.STATUS_ENDED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])

    def regenerate_key(self):
        self.stream_key = _generate_stream_key()
        if self.status == self.STATUS_LIVE:
            self.status = self.STATUS_OFFLINE
        self.save(update_fields=['stream_key', 'status'])
