"""The upload cap must measure the body, not a number the client supplied.

`cases.import_views._read_upload` gated on `upload.size`, which for an
in-memory upload is derived from the request's Content-Length. Two ways past
it: understate the header, or omit it so `size` is falsy and the guard's
leading `if upload.size and ...` skipped the comparison outright.

`contacts.import_views` already measures `len(file_bytes)` after `read()` and
says why in its docstring. This pins the cases twin to the same behaviour.

Exercised against the helper rather than over HTTP because the point is what
the cap trusts. Django's own test client computes an honest size, so a request
built through it cannot express the lie being defended against.
"""

import io

import pytest

from cases.import_views import MAX_UPLOAD_BYTES, _read_upload


class _LyingUpload:
    """An upload whose declared size does not match the bytes it hands over."""

    def __init__(self, payload: bytes, declared_size):
        self.name = "cases.csv"
        self.size = declared_size
        self._buf = io.BytesIO(payload)

    def read(self):
        return self._buf.read()


class _Request:
    def __init__(self, upload):
        self.FILES = {"file": upload}


OVERSIZED = b"a" * (MAX_UPLOAD_BYTES + 1)


@pytest.mark.parametrize(
    "declared_size,label",
    [
        (0, "a zero Content-Length skipped the check entirely"),
        (None, "an absent Content-Length skipped the check entirely"),
        (10, "an understated Content-Length passed the check"),
    ],
)
def test_an_oversized_body_is_refused_whatever_the_client_declares(
    declared_size, label
):
    file_bytes, error = _read_upload(_Request(_LyingUpload(OVERSIZED, declared_size)))
    assert file_bytes is None, label
    assert error is not None
    assert error.status_code == 400


def test_a_body_within_the_cap_is_still_accepted():
    """The True direction. A cap that rejects everything is not a cap."""
    payload = b"name,status\nA case,New\n"
    file_bytes, error = _read_upload(_Request(_LyingUpload(payload, len(payload))))
    assert error is None
    assert file_bytes == payload


def test_an_overstated_size_does_not_reject_a_small_body():
    """The cap follows the bytes, so a large declared size is not enough to fail."""
    payload = b"name,status\nA case,New\n"
    file_bytes, error = _read_upload(
        _Request(_LyingUpload(payload, MAX_UPLOAD_BYTES + 1))
    )
    assert error is None
    assert file_bytes == payload
