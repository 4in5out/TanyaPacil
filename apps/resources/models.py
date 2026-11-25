from django.db import models
from django.utils.text import slugify

from .services.extractor import extract_text_from_pdf, extract_text_from_url


class ResourceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=16, default='📘', help_text='Emoji icon shown in the VN Resources panel')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Resource Category'
        verbose_name_plural = 'Resource Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icon} {self.name}"


class Resource(models.Model):
    TYPE_PDF = 'PDF'
    TYPE_EXTERNAL = 'EXTERNAL'
    TYPE_NOTE = 'NOTE'

    RESOURCE_TYPE_CHOICES = [
        (TYPE_PDF, 'PDF Document (Slides / Module)'),
        (TYPE_EXTERNAL, 'External Source (GFG / W3Schools / Docs)'),
        (TYPE_NOTE, 'Manual Study Note'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(
        ResourceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resources',
    )
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default=TYPE_PDF,
    )
    file = models.FileField(
        upload_to='resources/pdfs/',
        blank=True,
        null=True,
        help_text='Upload a PDF file (text will be extracted automatically on save).',
    )
    source_url = models.URLField(
        blank=True,
        help_text='External URL such as GeeksforGeeks or W3Schools.',
    )
    summary = models.TextField(
        blank=True,
        help_text='Short description shown to students in the Resources drawer.',
    )
    extracted_text = models.TextField(
        blank=True,
        help_text='Text indexed for Pak Chill. Auto-populated for PDFs/URLs if left blank.',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__name', 'title']

    def extract_content(self) -> str:
        if self.resource_type == self.TYPE_PDF and self.file:
            return extract_text_from_pdf(self.file.path)
        if self.resource_type == self.TYPE_EXTERNAL and self.source_url:
            return extract_text_from_url(self.source_url)
        return self.extracted_text

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.extracted_text:
            extracted = self.extract_content()
            if extracted:
                self.extracted_text = extracted
                super().save(update_fields=['extracted_text'])

    @property
    def text_length(self) -> int:
        return len(self.extracted_text or '')

    def __str__(self):
        return f"[{self.get_resource_type_display().split(' ')[0]}] {self.title}"
