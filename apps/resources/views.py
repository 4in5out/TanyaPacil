from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Resource


@require_GET
def resource_list_api(request):
    resources = (
        Resource.objects.filter(is_active=True)
        .select_related('category')
        .order_by('category__name', 'title')
    )
    data = [
        {
            'id': r.id,
            'title': r.title,
            'category': r.category.name if r.category else 'General',
            'category_icon': r.category.icon if r.category else '📘',
            'resource_type': r.resource_type,
            'summary': r.summary,
            'source_url': r.source_url,
            'file_url': r.file.url if r.file else '',
            'indexed': bool(r.extracted_text),
        }
        for r in resources
    ]
    return JsonResponse({'resources': data})
