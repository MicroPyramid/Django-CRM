"""Make `is_organization_admin` agree with `role` on every existing row.

The two columns are one binary fact stored twice (`ROLES` is ADMIN/USER and
nothing else) and used to be settable independently. `common.permissions
.is_org_admin` now reads `role` alone and `Profile.save` derives the column, so
this changes nobody's access: it only stops the stored value from contradicting
the role in the three payloads that still return it (`/api/profile/`, the org
list, the login response).

Without this, a row written before the change keeps its stale value until that
profile happens to be saved, and a client reading `is_organization_admin: true`
off a member would show an admin badge for someone the API treats as a member.

The dev database had zero disagreeing rows when this was written. Production
may differ, which is the reason to run it rather than assume.
"""

from django.db import migrations


def sync_flag_to_role(apps, schema_editor):
    Profile = apps.get_model("common", "Profile")
    Profile.objects.filter(role="ADMIN", is_organization_admin=False).update(
        is_organization_admin=True
    )
    Profile.objects.exclude(role="ADMIN").filter(is_organization_admin=True).update(
        is_organization_admin=False
    )


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0034_rls_pipeline_tables"),
    ]

    # No reverse: the pre-migration values are not recoverable, and restoring a
    # disagreement would restore a lie rather than a capability. Nothing reads
    # the column for authorization any more, so leaving it consistent on a
    # rollback is correct.
    operations = [
        migrations.RunPython(sync_flag_to_role, migrations.RunPython.noop),
    ]
