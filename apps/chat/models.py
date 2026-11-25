import uuid
from django.db import models

from apps.resources.models import Resource


class ChatSession(models.Model):
    session_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=200, default='New Study Session')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({str(self.session_key)[:8]})"


class ChatMessage(models.Model):
    SENDER_USER = 'user'
    SENDER_BOT = 'bot'
    SENDER_CHOICES = [
        (SENDER_USER, 'Student'),
        (SENDER_BOT, 'Pak Chill'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    cited_resources = models.ManyToManyField(Resource, blank=True, related_name='citations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        preview = (self.content[:45] + '...') if len(self.content) > 45 else self.content
        return f"[{self.sender}] {preview}"
