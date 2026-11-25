from django.contrib import admin, messages

from .models import Resource, ResourceCategory


@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resource_type', 'is_active', 'indexed_chars', 'updated_at')
    list_filter = ('resource_type', 'category', 'is_active')
    search_fields = ('title', 'summary', 'extracted_text', 'source_url')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['re_extract_text']

    fieldsets = (
        (None, {
            'fields': ('title', 'category', 'resource_type', 'is_active'),
        }),
        ('Source Material', {
            'fields': ('file', 'source_url', 'summary'),
            'description': 'Upload a PDF or enter an external URL (e.g., GFG / W3Schools).',
        }),
        ('Indexed Knowledge (Used by Pak Chill)', {
            'fields': ('extracted_text',),
            'description': 'Leave blank on first save to auto-extract from PDF or URL, or paste/edit notes manually.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Indexed Chars')
    def indexed_chars(self, obj):
        return f"{obj.text_length:,}"

    @admin.action(description='Re-extract text from selected PDFs / URLs')
    def re_extract_text(self, request, queryset):
        updated = 0
        for resource in queryset:
            text = resource.extract_content()
            if text:
                resource.extracted_text = text
                resource.save(update_fields=['extracted_text', 'updated_at'])
                updated += 1
        self.message_user(
            request,
            f"Successfully re-extracted text for {updated} resource(s).",
            level=messages.SUCCESS,
        )
