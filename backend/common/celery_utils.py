"""
Celery utilities for multi-tenancy support.

Provides org-aware task execution to ensure background tasks
respect organization context and data isolation.
"""

import logging
from functools import wraps

from celery import shared_task
from django.db import connection

logger = logging.getLogger(__name__)


class OrgContext:
    """
    Context manager for setting organization context in background tasks.

    Usage:
        with OrgContext(org_id):
            # All queries here will have org context
            leads = Lead.objects.filter(org_id=org_id)

    For RLS (when implemented):
        Sets PostgreSQL app.current_org parameter for Row-Level Security.
    """

    def __init__(self, org_id):
        self.org_id = str(org_id) if org_id else None

    def __enter__(self):
        if self.org_id:
            # Set PostgreSQL session variable for RLS (future use)
            # This will be used when Row-Level Security is enabled
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET app.current_org = %s", [self.org_id])
            except Exception as e:
                # RLS might not be configured yet - this is expected
                logger.debug(f"Could not set app.current_org: {e}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Reset the context
        if self.org_id:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("RESET app.current_org")
            except Exception:
                pass

        return False


def org_aware_task(func):
    """
    Decorator for Celery tasks that require organization context.

    The first argument to the task must be org_id.

    Usage:
        @shared_task
        @org_aware_task
        def my_task(org_id, other_arg):
            # org_id is automatically validated and context is set
            pass

    Example:
        @shared_task
        @org_aware_task
        def send_org_report(org_id, report_type):
            org = Org.objects.get(id=org_id)
            # Generate report for this org
            pass
    """

    @wraps(func)
    def wrapper(org_id, *args, **kwargs):
        from common.models import Org

        # Validate org exists
        try:
            org = Org.objects.get(id=org_id, is_active=True)
        except Org.DoesNotExist:
            logger.error(
                f"Task {func.__name__} failed: Org {org_id} not found or inactive"
            )
            raise ValueError(f"Invalid org_id: {org_id}")

        # Execute with org context
        with OrgContext(org_id):
            logger.info(f"Executing {func.__name__} for org {org_id}")
            return func(org_id, *args, **kwargs)

    return wrapper


def require_org_id(func):
    """
    Simple decorator that ensures org_id is provided to a task.

    Usage:
        @shared_task
        @require_org_id
        def my_task(org_id, data):
            pass
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        org_id = kwargs.get("org_id") or (args[0] if args else None)

        if not org_id:
            raise ValueError(f"Task {func.__name__} requires org_id parameter")

        return func(*args, **kwargs)

    return wrapper


# Example org-aware tasks


@shared_task
@org_aware_task
def cleanup_expired_sessions(org_id):
    """
    Clean up expired session tokens for an organization.

    Usage:
        cleanup_expired_sessions.delay(org_id=str(org.id))
    """
    from common.models import SessionToken

    deleted_count, _ = SessionToken.objects.filter(
        user__profiles__org_id=org_id, is_active=False
    ).delete()

    logger.info(f"Cleaned up {deleted_count} expired sessions for org {org_id}")
    return deleted_count


@shared_task
@org_aware_task
def generate_org_activity_report(org_id, days=30):
    """
    Generate activity report for an organization.

    Usage:
        generate_org_activity_report.delay(org_id=str(org.id), days=30)
    """
    from datetime import timedelta

    from django.utils import timezone

    from common.models import Activity

    start_date = timezone.now() - timedelta(days=days)

    activities = Activity.objects.filter(org_id=org_id, created_at__gte=start_date)

    report = {
        "org_id": org_id,
        "period_days": days,
        "total_activities": activities.count(),
        "by_action": {},
        "by_entity": {},
    }

    for activity in activities:
        # Count by action
        action = activity.action
        report["by_action"][action] = report["by_action"].get(action, 0) + 1

        # Count by entity type
        entity = activity.entity_type
        report["by_entity"][entity] = report["by_entity"].get(entity, 0) + 1

    logger.info(
        f"Generated activity report for org {org_id}: {report['total_activities']} activities"
    )
    return report


@shared_task
def send_email_with_org_context(org_id, user_id, template_name, subject, context):
    """
    Send email with organization branding/context.

    Usage:
        send_email_with_org_context.delay(
            org_id=str(org.id),
            user_id=str(user.id),
            template_name='welcome_email.html',
            subject='Welcome to Our CRM',
            context={'custom_key': 'value'}
        )
    """
    from django.conf import settings
    from django.core.mail import EmailMessage
    from django.template.loader import render_to_string

    from common.models import Org, User

    try:
        org = Org.objects.get(id=org_id)
        user = User.objects.get(id=user_id)
    except (Org.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Email send failed: {e}")
        raise

    # Add org context to email template
    email_context = {
        "org_name": org.name,
        "user_email": user.email,
        "domain": settings.DOMAIN_NAME,
        **context,
    }

    html_content = render_to_string(template_name, context=email_context)

    msg = EmailMessage(
        subject,
        html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.content_subtype = "html"
    msg.send()

    logger.info(f"Sent email '{subject}' to {user.email} for org {org.name}")


# Batch processing utilities


@shared_task
@org_aware_task
def batch_process_org_data(org_id, model_name, processor_func, batch_size=100):
    """
    Process org data in batches to avoid memory issues.

    Usage:
        batch_process_org_data.delay(
            org_id=str(org.id),
            model_name='leads.Lead',
            processor_func='leads.tasks.process_lead',
            batch_size=100
        )
    """
    from importlib import import_module

    from django.apps import apps

    # Get model
    app_label, model_class = model_name.rsplit(".", 1)
    Model = apps.get_model(app_label, model_class)

    # Get processor function
    module_path, func_name = processor_func.rsplit(".", 1)
    module = import_module(module_path)
    processor = getattr(module, func_name)

    # Process in batches
    queryset = Model.objects.filter(org_id=org_id)
    total = queryset.count()
    processed = 0

    for i in range(0, total, batch_size):
        batch = queryset[i : i + batch_size]
        for obj in batch:
            processor(obj)
            processed += 1

        logger.info(f"Processed {processed}/{total} {model_name} for org {org_id}")

    return processed
