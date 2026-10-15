"""A CSV import refuses an oversized upload without loading it into memory.

Django has already spooled the request to a temp file on disk by the time a
view runs, so the only memory an upload costs is what the view reads. The
contacts and cases importers called `upload.read()` with no limit and only
then compared the length with the 5 MB cap, so a 1 GB file became 1 GB of
worker memory before it was refused; a few at once could get the workers
OOM-killed (issue #828). Leads already stopped reading one byte past the cap.

The cap is patched down to 1 MB and the upload is 8 MB, so an unbounded read
shows up as a peak of at least 8 MB.
"""

import tracemalloc
from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.files.uploadedfile import TemporaryUploadedFile

from cases import import_views as cases_import
from contacts import import_views as contacts_import
from leads.views import import_views as leads_import

CAP = 1024 * 1024
UPLOAD = 8 * CAP


@pytest.fixture
def oversized_upload():
    upload = TemporaryUploadedFile("big.csv", "text/csv", UPLOAD, "utf-8")
    chunk = b"a" * CAP
    for _ in range(UPLOAD // CAP):
        upload.write(chunk)
    upload.seek(0)
    yield upload
    upload.close()


@pytest.mark.parametrize(
    "module", [contacts_import, cases_import, leads_import], ids=lambda m: m.__name__
)
def test_an_oversized_upload_is_refused_without_reading_it_whole(
    module, oversized_upload
):
    request = SimpleNamespace(FILES={"file": oversized_upload})
    with mock.patch.object(module, "MAX_UPLOAD_BYTES", CAP):
        tracemalloc.start()
        try:
            file_bytes, problem = module._read_upload(request)
            _, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()

    assert file_bytes is None
    assert problem is not None
    assert peak < 2 * CAP, f"read {peak} bytes into memory for a {CAP} byte cap"
