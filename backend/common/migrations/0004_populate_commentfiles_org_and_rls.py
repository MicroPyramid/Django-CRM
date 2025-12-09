# Generated migration - Populate CommentFiles org and enable RLS

from django.db import migrations

from common.rls import get_enable_policy_sql


def populate_org_from_comment(apps, schema_editor):
    """
    Populate the org field in CommentFiles from parent Comment's org.
    """
    CommentFiles = apps.get_model("common", "CommentFiles")
    for cf in CommentFiles.objects.select_related("comment").all():
        if cf.comment and cf.comment.org_id:
            cf.org_id = cf.comment.org_id
            cf.save(update_fields=["org_id"])


def enable_rls_on_commentfiles(apps, schema_editor):
    """
    Enable RLS policy on commentFiles table.
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        # Check if table has org_id column
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'commentFiles' AND column_name = 'org_id'
            """
        )
        if cursor.fetchone():
            cursor.execute(get_enable_policy_sql("commentFiles"))


def disable_rls_on_commentfiles(apps, schema_editor):
    """
    Reverse: Disable RLS policy on commentFiles table.
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    from common.rls import get_disable_policy_sql

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(get_disable_policy_sql("commentFiles"))


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0003_add_org_to_commentfiles"),
    ]

    operations = [
        migrations.RunPython(
            populate_org_from_comment,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            enable_rls_on_commentfiles,
            reverse_code=disable_rls_on_commentfiles,
        ),
    ]
