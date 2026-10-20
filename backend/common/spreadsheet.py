"""Read an uploaded .xlsx or .csv file into a plain table of text cells.

Error messages never include cell values, file names or library exception
text, since any of those can quote the uploaded content.
"""

import csv
import datetime
import io
import re
import zipfile
from dataclasses import dataclass

import openpyxl

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_XLSX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_XLSX_ENTRIES = 1000
MAX_COLUMNS = 1000

# A sheet's declared size (its <dimension> element) is not trusted: it can
# claim a million rows and 16,384 columns while holding one cell, and the
# reader would pad every row to that size. So it is discarded and each row is
# read only as wide as its own last cell, this many blank rows in a row end the
# data, and more than 4 * max_rows + 1000 rows read in all, blank ones
# included, is refused.
_XLSX_BLANK_RUN = 1000

_XLSX_UNREADABLE = (
    "That .xlsx file could not be opened. Save it again, or export it as .csv."
)
_XLSX_TOO_LARGE = "That .xlsx file is too large to read."

# The guard our exports put on a cell a spreadsheet would run as a formula
# (`common/csv_export.py`, the web's `csvCell`): one leading apostrophe. A
# re-uploaded export loses that one apostrophe, and only that one.
_FORMULA_GUARD = re.compile(r"'+[=+\-@]")


class SpreadsheetError(Exception):
    """Raised with a sentence that is safe to show to the user."""


@dataclass(frozen=True)
class Table:
    headers: list[str]
    rows: list[list[str]]


def _cell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, datetime.datetime):
        if value.time() == datetime.time(0, 0):
            return value.date().isoformat()
        return value.isoformat(sep=" ", timespec="minutes")
    if isinstance(value, datetime.date):
        return value.isoformat()
    text = str(value).strip()
    return text[1:] if _FORMULA_GUARD.match(text) else text


def _build_table(raw_rows, max_rows: int, exact_count: bool) -> Table:
    """Turn an iterable of cell sequences into a Table.

    Blank rows are dropped and the first non-blank row is the header, less its
    trailing empty cells. The table is as wide as its widest cell holding data:
    a value under no header widens it, and the headers are padded with "" so
    the column reaches the matching step unnamed instead of vanishing. Only
    empty cells past that width are dropped, which is what keeps a sheet that
    declares 16,384 columns of formatting from costing 16,384 cells a row.
    Wider than MAX_COLUMNS is refused.

    With exact_count False (an .xlsx), iteration stops as soon as the row limit
    is exceeded, a run of _XLSX_BLANK_RUN blank rows ends the data, and reading
    more than 4 * max_rows + 1000 rows in all is refused.
    """
    too_many_rows = f"Too many rows (more than {max_rows}); the limit is {max_rows}."
    too_many_columns = (
        f"Too many columns (more than {MAX_COLUMNS}); the limit is {MAX_COLUMNS}."
    )
    raw_limit = 4 * max_rows + 1000
    headers = None
    width = None
    rows = []
    read = 0
    blank_run = 0
    for raw in raw_rows:
        if not exact_count:
            read += 1
            if read > raw_limit:
                raise SpreadsheetError(too_many_rows)
        if width is not None and len(raw) > width:
            head = raw[:width]
            # A row padded with None past the data costs one C-level count and
            # no copy of the padding; only a row holding something there is
            # looked at cell by cell.
            if raw.count(None) - head.count(None) != len(raw) - width:
                extra = raw[width:]
                last = max(
                    (i for i, c in enumerate(extra) if _cell_text(c)), default=-1
                )
                if last >= 0:
                    width += last + 1
                    if width > MAX_COLUMNS:
                        raise SpreadsheetError(too_many_columns)
                    headers.extend([""] * (width - len(headers)))
            raw = raw[:width]
        # A row the reader padded with nothing but None costs no conversions.
        if raw.count(None) == len(raw):
            cells = []
        else:
            cells = [_cell_text(c) for c in raw]
        if not any(cells):
            blank_run += 1
            if not exact_count and blank_run >= _XLSX_BLANK_RUN:
                break
            continue
        blank_run = 0
        if headers is None:
            while not cells[-1]:
                cells.pop()
            if len(cells) > MAX_COLUMNS:
                raise SpreadsheetError(too_many_columns)
            headers = cells
            width = len(cells)
            continue
        rows.append(cells)
        if not exact_count and len(rows) > max_rows:
            raise SpreadsheetError(too_many_rows)
    if headers is None:
        raise SpreadsheetError("The file is empty.")
    if len(rows) > max_rows:
        raise SpreadsheetError(f"Too many rows ({len(rows)}); the limit is {max_rows}.")
    return Table(headers=headers, rows=rows)


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def _read_csv(data: bytes, max_rows: int) -> Table:
    text = _decode(data)
    # Postgres refuses NUL in any string parameter, so one would 500 the insert.
    if "\x00" in text:
        raise SpreadsheetError(
            "The file could not be read: it contains NUL characters."
        )
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    try:
        return _build_table(csv.reader(io.StringIO(text), dialect), max_rows, True)
    except csv.Error:
        # A field over the csv module's size limit lands here.
        raise SpreadsheetError("The file could not be read.") from None


def _check_zip(data: bytes) -> None:
    buf = io.BytesIO(data)
    if not zipfile.is_zipfile(buf):
        raise SpreadsheetError(_XLSX_UNREADABLE)
    try:
        with zipfile.ZipFile(buf) as zf:
            infos = zf.infolist()
    except (zipfile.BadZipFile, OSError):
        raise SpreadsheetError(_XLSX_UNREADABLE) from None
    if (
        len(infos) > MAX_XLSX_ENTRIES
        or sum(i.file_size for i in infos) > MAX_XLSX_UNCOMPRESSED_BYTES
    ):
        raise SpreadsheetError(_XLSX_TOO_LARGE)


def _read_xlsx(data: bytes, max_rows: int) -> Table:
    _check_zip(data)
    wb = None
    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(data), read_only=True, data_only=True, keep_links=False
        )
        sheet = wb.worksheets[0]
        # Forget the declared size, so each row is only as wide as its own
        # last cell: nothing is padded out to a claimed 16,384 columns, and a
        # value past MAX_COLUMNS is seen (and refused) rather than clipped.
        sheet.reset_dimensions()
        rows = sheet.iter_rows(values_only=True)
        return _build_table(rows, max_rows, False)
    except SpreadsheetError:
        raise
    except Exception:
        # Library messages can quote file content, so none is passed on.
        raise SpreadsheetError(_XLSX_UNREADABLE) from None
    finally:
        if wb is not None:
            wb.close()


def read_table(name: str, data: bytes, max_rows: int) -> Table:
    extension = (name or "").rsplit(".", 1)[-1].lower() if "." in (name or "") else ""
    if extension not in ("csv", "xlsx"):
        raise SpreadsheetError("Save it as .xlsx or .csv and try again.")
    if not data:
        raise SpreadsheetError("The file is empty.")
    if extension == "csv":
        return _read_csv(data, max_rows)
    return _read_xlsx(data, max_rows)


def read_upload(request, max_rows: int) -> Table:
    upload = request.FILES.get("file")
    if not upload:
        raise SpreadsheetError("No file uploaded (expected field 'file')")
    # One byte past the cap is enough to refuse without loading the whole body.
    data = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise SpreadsheetError("File exceeds the 5 MB upload limit")
    return read_table(upload.name, data, max_rows)
