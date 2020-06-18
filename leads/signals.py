# from django.db.models.signals import post_delete, post_save
# from django.dispatch import receiver

# from common.models import User
# from leads.models import Lead


# @receiver([post_delete, post_save], sender=User)
# def update_cache_for_leads_list_users(sender, **kwargs):
#     print('after registering it in the app')
#     lead_users = User.objects.filter(
#         is_active=True).order_by('email').values('id', 'email')
#     cache.set('lead_form_users', lead_users, 60*60)

# @receiver([post_delete, post_save], sender=Lead)
# def update_cache_for_leads_list_page(sender, **kwargs):
#     queryset = Lead.objects.all().exclude(status='converted').select_related('created_by'
#             ).prefetch_related('tags', 'assigned_to',)
#     open_leads = queryset.exclude(status='closed')
#     close_leads = queryset.filter(status='closed')
#     cache.set('admin_leads_open_queryset', open_leads, 60*60)
#     cache.set('admin_leads_close_queryset', close_leads, 60*60)