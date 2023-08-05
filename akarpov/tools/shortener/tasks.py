from celery import shared_task

from akarpov.tools.shortener.models import Link, LinkViewMeta


@shared_task
def save_view_meta(pk, ip, user_agent, user_id):
    link = Link.objects.get(pk=pk)
    meta = LinkViewMeta(link=link, ip=ip, user_agent=user_agent)
    if user_id:
        meta.user_id = user_id
    meta.save()
    link.viewed += 1
    link.save(update_fields=["viewed"])
    return
