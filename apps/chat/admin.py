from django.contrib import admin

from .models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('sender', 'content', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'session_key', 'created_at', 'updated_at')
    search_fields = ('title', 'session_key')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'sender', 'short_content', 'created_at')
    list_filter = ('sender', 'created_at')
    search_fields = ('content',)

    @admin.display(description='Message')
    def short_content(self, obj):
        return (obj.content[:70] + '...') if len(obj.content) > 70 else obj.content
