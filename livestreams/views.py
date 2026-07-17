import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import LiveStream

logger = logging.getLogger(__name__)


@login_required
def go_live(request):
    """Creator dashboard: create/manage their live stream."""
    stream = LiveStream.objects.filter(creator=request.user).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            if not title:
                title = f"{request.user.username}'s Live"
            if stream:
                stream.title = title
                stream.save(update_fields=['title'])
            else:
                stream = LiveStream.objects.create(creator=request.user, title=title)

        elif action == 'regenerate_key' and stream:
            stream.regenerate_key()

        return redirect('go-live')

    return render(request, 'cms/go_live.html', {'stream': stream})


@require_GET
def livestream_page(request, pk):
    """Public viewer page for a live stream."""
    stream = get_object_or_404(LiveStream, pk=pk)
    return render(request, 'cms/livestream.html', {'stream': stream})


@require_GET
def api_active_streams(request):
    """Return all currently live streams."""
    streams = LiveStream.objects.filter(status=LiveStream.STATUS_LIVE).values(
        'id', 'title', 'creator__username', 'stream_key', 'started_at'
    )
    return JsonResponse({'streams': list(streams)})


@require_GET
def api_stream_status(request, pk):
    """Return current status of a stream (for viewer-side polling)."""
    stream = get_object_or_404(LiveStream, pk=pk)
    return JsonResponse({
        'id': stream.pk,
        'title': stream.title,
        'status': stream.status,
        'stream_key': stream.stream_key,
        'started_at': stream.started_at.isoformat() if stream.started_at else None,
    })


@csrf_exempt
def srs_on_publish(request):
    """
    SRS HTTP callback: fired when an RTMP publisher connects.
    Validates the stream key against a known LiveStream.
    Returns {"code": 0} to accept or {"code": 1} to reject.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'code': 1})

    stream_name = data.get('stream', '')
    logger.info('SRS on_publish: stream=%s', stream_name)

    try:
        stream = LiveStream.objects.get(stream_key=stream_name)
    except LiveStream.DoesNotExist:
        logger.warning('SRS on_publish: unknown stream key %s', stream_name)
        return JsonResponse({'code': 1})

    stream.go_live()
    logger.info('LiveStream %s (%s) is now LIVE', stream.pk, stream.title)
    return JsonResponse({'code': 0})


@csrf_exempt
def srs_on_unpublish(request):
    """
    SRS HTTP callback: fired when an RTMP publisher disconnects.
    Marks the stream as ended.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'code': 0})

    stream_name = data.get('stream', '')
    logger.info('SRS on_unpublish: stream=%s', stream_name)

    LiveStream.objects.filter(stream_key=stream_name, status=LiveStream.STATUS_LIVE).update(
        status=LiveStream.STATUS_ENDED
    )
    return JsonResponse({'code': 0})
