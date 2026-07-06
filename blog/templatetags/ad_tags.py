from django import template
from django.utils import timezone
from django.db.models import Q, F
import random
from blog.models import Advertisement

register = template.Library()

@register.simple_tag
def get_ad(position):
    now = timezone.now()
    active_ads = Advertisement.objects.filter(
        position=position,
        is_active=True
    ).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now)
    ).filter(
        Q(ends_at__isnull=True) | Q(ends_at__gte=now)
    )
    
    if not active_ads.exists():
        return None
        
    ad = random.choice(list(active_ads))
    
    # Increment impression atomically in the database
    Advertisement.objects.filter(pk=ad.pk).update(impressions=F('impressions') + 1)
    
    # Update the local instance in case the template queries it
    ad.impressions += 1
    
    return ad
