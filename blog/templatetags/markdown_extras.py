import markdown
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='markdownify')
def markdownify(value):
    if not value:
        return ""
    # Safe markdown parsing with table support, fencing, and TOC
    return mark_safe(markdown.markdown(
        value,
        extensions=['extra', 'toc']
    ))
