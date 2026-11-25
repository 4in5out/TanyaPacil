import json
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ChatMessage, ChatSession
from .services.gemini_client import ask_pak_chill
from .services.retriever import retrieve_relevant_resources


def _find_custom_asset(rel_folder: str, base_name: str, extensions: tuple[str, ...]) -> str:
    """Detect drop-in custom art/audio files under static/assets/ automatically."""
    static_root = Path(settings.BASE_DIR) / 'static' / 'assets' / rel_folder
    for ext in extensions:
        candidate = static_root / f"{base_name}.{ext}"
        if candidate.exists():
            return f"{settings.STATIC_URL}assets/{rel_folder}/{base_name}.{ext}"
    return ''


def _get_or_create_session(request) -> ChatSession:
    session_key = request.session.get('pak_chill_session_key')
    if session_key:
        session = ChatSession.objects.filter(session_key=session_key).first()
        if session:
            return session
    session = ChatSession.objects.create(title='Classroom Study Session')
    request.session['pak_chill_session_key'] = str(session.session_key)
    return session


@ensure_csrf_cookie
def index(request):
    session = _get_or_create_session(request)
    custom_assets = {
        'bg_video': _find_custom_asset('bg', 'classroom', ('mp4', 'webm')),
        'bg_image': _find_custom_asset('bg', 'classroom', ('webp', 'gif', 'png', 'jpg', 'jpeg')),
        'mascot_idle': _find_custom_asset('mascot', 'idle', ('webp', 'gif', 'png')),
        'mascot_thinking': _find_custom_asset('mascot', 'thinking', ('webp', 'gif', 'png')),
        'mascot_answering': _find_custom_asset('mascot', 'answering', ('webp', 'gif', 'png')),
        'bgm_audio': _find_custom_asset('audio', 'bgm', ('mp3', 'ogg', 'wav')),
        'voice_audio': _find_custom_asset('audio', 'voice_blip', ('wav', 'mp3', 'ogg')),
    }
    starter_prompts = [
        "Bedanya list, tuple, sama dictionary di Python apa?",
        "Jelasin konsep recursion dengan contoh simpel dong!",
        "Kenapa kodingan Python aku kena IndexError?",
        "Cara pakai Git & GitLab Pacil dari awal gimana?",
    ]
    return render(
        request,
        'chat/index.html',
        {
            'session_key': str(session.session_key),
            'custom_assets_json': json.dumps(custom_assets),
            'starter_prompts': starter_prompts,
        },
    )


@require_POST
def send_message_api(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    user_text = (payload.get('message') or '').strip()
    if not user_text:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)

    session = _get_or_create_session(request)

    # Fetch recent messages before saving the new one so we don't duplicate it in the prompt
    recent_messages = list(session.messages.order_by('-created_at')[:6])
    recent_messages.reverse()

    ChatMessage.objects.create(
        session=session,
        sender=ChatMessage.SENDER_USER,
        content=user_text,
    )

    if session.title == 'Classroom Study Session':
        session.title = user_text[:60]
        session.save(update_fields=['title', 'updated_at'])

    retrieved = retrieve_relevant_resources(user_text, top_k=4)
    reply_text = ask_pak_chill(user_text, retrieved, recent_messages)

    bot_msg = ChatMessage.objects.create(
        session=session,
        sender=ChatMessage.SENDER_BOT,
        content=reply_text,
    )

    unique_resources = []
    seen_ids = set()
    for chunk in retrieved:
        if chunk.resource.id not in seen_ids:
            seen_ids.add(chunk.resource.id)
            unique_resources.append(chunk.resource)

    if unique_resources:
        bot_msg.cited_resources.set(unique_resources)

    citations = [
        {
            'id': r.id,
            'title': r.title,
            'resource_type': r.resource_type,
            'source_url': r.source_url,
            'file_url': r.file.url if r.file else '',
        }
        for r in unique_resources
    ]

    return JsonResponse({
        'reply': reply_text,
        'citations': citations,
        'session_key': str(session.session_key),
        'message_id': bot_msg.id,
    })


@require_GET
def history_api(request):
    session = _get_or_create_session(request)
    msgs = session.messages.prefetch_related('cited_resources').all()
    history = [
        {
            'id': m.id,
            'sender': m.sender,
            'content': m.content,
            'created_at': m.created_at.strftime('%H:%M'),
            'citations': [
                {
                    'title': r.title,
                    'resource_type': r.resource_type,
                    'source_url': r.source_url,
                    'file_url': r.file.url if r.file else '',
                }
                for r in m.cited_resources.all()
            ],
        }
        for m in msgs
    ]
    return JsonResponse({'session_key': str(session.session_key), 'messages': history})


@require_POST
def reset_session_api(request):
    session = ChatSession.objects.create(title='Classroom Study Session')
    request.session['pak_chill_session_key'] = str(session.session_key)
    return JsonResponse({'session_key': str(session.session_key), 'status': 'reset'})
