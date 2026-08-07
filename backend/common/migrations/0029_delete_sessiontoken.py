"""Drop the unused `session_token` table.

`SessionToken` was added as "Phase 3: JWT Token Tracking" but was never wired
up, nothing in any view, middleware, serializer, or task ever created, read,
or revoked a row. Its only consumer was a Django admin page listing a
permanently empty table, which read as a working session-revocation feature
that did not exist.

Real refresh-token revocation now lives in simplejwt's `token_blacklist` app,
which `OrgAwareTokenRefreshView` writes to on every rotation, so this model has
no remaining purpose.
"""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0028_restamp_rls_policies"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="sessiontoken",
            name="session_tok_user_id_ce3d01_idx",
        ),
        migrations.RemoveIndex(
            model_name="sessiontoken",
            name="session_tok_token_j_a0ab6c_idx",
        ),
        migrations.RemoveIndex(
            model_name="sessiontoken",
            name="session_tok_expires_08e0bc_idx",
        ),
        migrations.DeleteModel(
            name="SessionToken",
        ),
    ]
