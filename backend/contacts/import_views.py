"""CSV import endpoints for contacts.

Preview reads the uploaded file and returns row-level validation results
without touching the DB. Commit re-runs validation and writes inside a single
transaction. Both endpoints are gated by
`common.permissions.can_mass_import` (admins, superusers, sales access) so
non-privileged members cannot mass-create contacts through this surface.

A request with a `mapping` form field ("auto", or JSON of column index to
field name) takes the column-matching path: any column names, .csv or .xlsx,
and rows that do not fit are skipped instead of refusing the file. Without
`mapping`, both endpoints keep the template-only behaviour.
"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.import_mapping import MappingError, read_mapped_upload
from common.permissions import HasOrgContext, can_mass_import
from common.spreadsheet import SpreadsheetError
from common.throttles import ImportThrottle
from contacts.services.csv_import import (
    CONTACT_FIELDS,
    CONTACT_SYNONYMS,
    MAX_ROWS,
    commit_mapped,
    commit_rows,
    parse_and_validate,
    preview_mapped,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB; matches the UI hint


def _read_upload(request):
    """Return (file_bytes, error_response). One of the two will be None.

    Reads at most one byte past the cap, so an oversized file is refused
    without being loaded into memory. Django has already spooled the body to
    disk by now; an unbounded `read()` pulled all of it into the worker. The
    cap is measured on the bytes read rather than on `upload.size`, so it does
    not depend on how the upload object was built.
    """
    upload = request.FILES.get("file")
    if not upload:
        return None, Response(
            {"error": True, "message": "No file uploaded (expected field 'file')"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    name = (upload.name or "").lower()
    if not name.endswith(".csv"):
        return None, Response(
            {"error": True, "message": "File must have a .csv extension"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    file_bytes = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        return None, Response(
            {"error": True, "message": "File exceeds the 5 MB upload limit"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return file_bytes, None


_MAPPABLE_FIELDS = frozenset(name for name, _label, _required in CONTACT_FIELDS)
_MAPPING_FIELD = serializers.CharField(
    required=False,
    help_text='"auto" to guess, or JSON of column index to field name.',
)


def _read_mapped(request):
    """Return ((table, mapping), None) or (None, error_response)."""
    try:
        mapped = read_mapped_upload(
            request, MAX_ROWS, CONTACT_SYNONYMS, _MAPPABLE_FIELDS
        )
    except (SpreadsheetError, MappingError) as exc:
        return None, Response(
            {"error": True, "message": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    return mapped, None


class ContactImportPreviewView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)
    throttle_classes = (ImportThrottle,)
    parser_classes = (MultiPartParser,)

    @extend_schema(
        tags=["contacts"],
        request=inline_serializer(
            name="ContactImportPreviewRequest",
            fields={"file": serializers.FileField(), "mapping": _MAPPING_FIELD},
        ),
        responses={
            200: inline_serializer(
                name="ContactImportPreviewResponse",
                fields={
                    "header_error": serializers.CharField(allow_null=True),
                    "valid": serializers.ListField(child=serializers.DictField()),
                    "errors": serializers.ListField(child=serializers.DictField()),
                    "summary": serializers.DictField(),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        if not can_mass_import(request.profile):
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if "mapping" in request.data:
            mapped, err = _read_mapped(request)
            if err is not None:
                return err
            preview = preview_mapped(*mapped, request.profile.org, request.profile)
            return Response(preview.to_dict(), status=status.HTTP_200_OK)
        file_bytes, err = _read_upload(request)
        if err is not None:
            return err
        result = parse_and_validate(file_bytes, request.profile.org, request.profile)
        return Response(result.to_dict(), status=status.HTTP_200_OK)


class ContactImportCommitView(APIView):
    permission_classes = (IsAuthenticated, HasOrgContext)
    throttle_classes = (ImportThrottle,)
    parser_classes = (MultiPartParser,)

    @extend_schema(
        tags=["contacts"],
        request=inline_serializer(
            name="ContactImportCommitRequest",
            fields={"file": serializers.FileField(), "mapping": _MAPPING_FIELD},
        ),
        responses={
            200: inline_serializer(
                name="ContactImportCommitResponse",
                fields={
                    "error": serializers.BooleanField(),
                    "created": serializers.IntegerField(),
                    "ids": serializers.ListField(child=serializers.CharField()),
                },
            )
        },
    )
    def post(self, request, *args, **kwargs):
        if not can_mass_import(request.profile):
            return Response(
                {"error": True, "message": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if "mapping" in request.data:
            mapped, err = _read_mapped(request)
            if err is not None:
                return err
            result = commit_mapped(*mapped, request.profile.org, request.profile)
            return Response(
                result,
                status=status.HTTP_400_BAD_REQUEST
                if result["error"]
                else status.HTTP_200_OK,
            )
        file_bytes, err = _read_upload(request)
        if err is not None:
            return err
        result = commit_rows(file_bytes, request.profile.org, request.profile)
        http_status = (
            status.HTTP_400_BAD_REQUEST if result.get("error") else status.HTTP_200_OK
        )
        return Response(result, status=http_status)
