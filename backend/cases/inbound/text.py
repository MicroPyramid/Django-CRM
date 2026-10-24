"""Plain text out of inbound mail: HTML to text, quoted history, and the
original message inside a hand-forwarded one.

Everything here reads text a stranger wrote, so it uses the standard library's
HTML parser and anchored, bounded patterns only, and never raises on odd input.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import unquote

# Big enough for any real notification; bounds the parser's work.
HTML_MAX = 500_000
FORWARD_DEPTH = 5

_SKIP_TAGS = {"head", "script", "style", "title", "template", "noscript", "svg"}
_BLOCK_TAGS = {
    "address", "article", "blockquote", "br", "dd", "div", "dt", "footer",
    "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li", "ol", "p", "pre",
    "section", "table", "tr", "ul",
}  # fmt: skip


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipping = 0
        self.link: tuple[str, int] | None = None

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self.skipping += 1
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")
        elif tag in ("td", "th"):
            self.parts.append(" ")
        elif tag == "a":
            self.link = (dict(attrs).get("href") or "", len(self.parts))

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS:
            self.skipping = max(0, self.skipping - 1)
        elif tag in _BLOCK_TAGS:
            self.parts.append("\n")
        elif tag == "a" and self.link is not None:
            href, start = self.link
            self.link = None
            # "Email Ravi" linking to mailto:ravi@... keeps the address.
            target = _link_target(href)
            shown = "".join(self.parts[start:])
            if target and target.lower() not in shown.lower():
                self.parts.append(f" ({target})")

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)


def _link_target(href: str) -> str:
    scheme, _, rest = href.strip().partition(":")
    if scheme.lower() not in ("mailto", "tel"):
        return ""
    return unquote(rest.split("?", 1)[0]).strip()


def html_to_text(html: str) -> str:
    parser = _TextParser()
    try:
        parser.feed((html or "")[:HTML_MAX])
        parser.close()
    except Exception:  # a malformed document still gives its text
        pass
    return tidy("".join(parser.parts))


def tidy(text: str) -> str:
    """One space between words, at most one blank line in a row."""
    lines = [" ".join(line.split()) for line in (text or "").splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


# ---------------------------------------------------------------------------
# Quoted history
# ---------------------------------------------------------------------------

_ON_WROTE = re.compile(r"On\b.{1,300}\bwrote:", re.IGNORECASE)
_ORIGINAL = re.compile(r"-{2,}\s*Original Message\s*-{2,}", re.IGNORECASE)
_RULE = re.compile(r"_{8,}")
_FROM_LINE = re.compile(r"\*?From\*?\s*:\s*\S", re.IGNORECASE)
_SENT_LINE = re.compile(r"\*?Sent\*?\s*:\s*\S", re.IGNORECASE)


def strip_quoted_history(text: str) -> str:
    """The new part of a reply: everything above its first quote header,
    without `>` lines."""
    lines = (text or "").splitlines()
    for i, line in enumerate(lines):
        if _starts_history(lines, i):
            lines = lines[:i]
            break
    kept = [line for line in lines if not line.lstrip().startswith(">")]
    return tidy("\n".join(kept))


def _starts_history(lines, i) -> bool:
    line = lines[i].strip()
    if line.startswith("On ") and (
        _ON_WROTE.fullmatch(line)
        or (
            i + 1 < len(lines) and _ON_WROTE.fullmatch(f"{line} {lines[i + 1].strip()}")
        )
    ):
        return True
    if _ORIGINAL.fullmatch(line):
        return True
    # Outlook's reply header, a rule line or "From:" with "Sent:" just below.
    # Portal notifications use both rules and "From:" labels on their own.
    following = [n.strip() for n in lines[i + 1 : i + 4]]
    if _RULE.fullmatch(line):
        return any(_FROM_LINE.match(n) for n in following[:2])
    if _FROM_LINE.match(line):
        return any(_SENT_LINE.match(n) for n in following)
    return False


# ---------------------------------------------------------------------------
# Forwarded messages
# ---------------------------------------------------------------------------

_FORWARD_MARKER = re.compile(
    r"-*\s*Forwarded message\s*-*|Begin forwarded message:?", re.IGNORECASE
)
# Forward prefixes in English and the common European clients.
_FORWARD_SUBJECT = re.compile(r"(?:(?:fwd?|fw|tr|wg|rv|vs|enc)\s*:\s*)+", re.IGNORECASE)
_HEADER = re.compile(
    r"\*?(From|Date|Sent|Subject|To|Cc|Reply-To)\*?\s*:\s*\*?\s*(.*)", re.IGNORECASE
)
_ANGLE_ADDRESS = re.compile(r"<\s*(?:mailto:)?([^<>\s]+@[^<>\s]+)\s*>")
_MAILTO_ADDRESS = re.compile(r"\[\s*mailto:([^\]\s]+@[^\]\s]+)\s*\]", re.IGNORECASE)
# The lookbehind starts a match only at the start of a run, which keeps a long
# run of address characters linear instead of quadratic.
ADDRESS = re.compile(
    r"(?<![A-Za-z0-9._%+'-])[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
)
HEADER_VALUE_MAX = 1000
# Real forwarded header blocks are 4 to 8 lines.
HEADER_BLOCK_MAX = 15


@dataclass
class Forwarded:
    name: str
    address: str
    reply_to: str
    reply_to_name: str
    subject: str
    body: str


def strip_forward_prefix(subject: str) -> str:
    return _FORWARD_SUBJECT.sub("", (subject or "").strip(), count=1).strip()


def innermost_forward(text: str, subject: str) -> Forwarded | None:
    """The original message inside a forward, following forwards of forwards.

    An explicit marker ("Forwarded message", "Begin forwarded message") is
    trusted anywhere; Outlook's "Original Message" or rule line, or a bare
    "From:" header block, only when the subject says it is a forward.
    """
    found = None
    for _ in range(FORWARD_DEPTH):
        inner = _forward_in(text, subject)
        if inner is None:
            break
        found = inner
        text, subject = inner.body, inner.subject or subject
    return found


def _forward_in(text, subject):
    lines = (text or "").splitlines()
    forwarded_subject = bool(_FORWARD_SUBJECT.match((subject or "").strip()))
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if _is_marker(line, forwarded_subject):
            start = i + 1
        elif forwarded_subject and _FROM_LINE.match(line):
            start = i
        else:
            i += 1
            continue
        found, end = _header_block(lines, start, forwarded_subject)
        if found is not None:
            return found
        # A failed block's lines are never read again, which keeps a body of
        # nothing but "From:" lines or markers linear.
        i = max(i + 1, end)
    return None


def _is_marker(line, forwarded_subject):
    return bool(
        _FORWARD_MARKER.fullmatch(line)
        or (forwarded_subject and (_ORIGINAL.fullmatch(line) or _RULE.fullmatch(line)))
    )


def _header_block(lines, start, forwarded_subject):
    """(the forwarded original, or None; the index after the last line read).

    At most HEADER_BLOCK_MAX lines are read as headers, each value is cut to
    HEADER_VALUE_MAX, and a marker line ends the block unread.
    """
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    headers: dict[str, list[str]] = {}
    sizes: dict[str, int] = {}
    last = None
    stop = min(len(lines), i + HEADER_BLOCK_MAX)
    while i < stop:
        line = lines[i].strip()[: 2 * HEADER_VALUE_MAX]
        if not line or _is_marker(line, forwarded_subject):
            break
        match = _HEADER.fullmatch(line)
        if match:
            last = match.group(1).lower()
            part = match.group(2).strip()
            if last in headers:
                last = None  # a repeated header: keep the first, skip its lines
        elif last is None:
            if not headers:
                break
            i += 1
            continue
        else:
            part = line
        if last is not None and sizes.get(last, 0) < HEADER_VALUE_MAX:
            headers.setdefault(last, []).append(part)
            sizes[last] = sizes.get(last, 0) + len(part) + 1
        i += 1
    values = {k: " ".join(v)[:HEADER_VALUE_MAX] for k, v in headers.items()}
    name, address = split_address(values.get("from", ""))
    if not address:
        return None, i
    while (
        i < len(lines)
        and lines[i].strip()
        and not _is_marker(lines[i].strip(), forwarded_subject)
    ):
        i += 1  # the rest of an over-long header block
    reply_name, reply_to = split_address(values.get("reply-to", ""))
    return (
        Forwarded(
            name=name,
            address=address,
            reply_to=reply_to,
            reply_to_name=reply_name,
            subject=values.get("subject", "").strip("* "),
            body="\n".join(lines[i:]),
        ),
        i,
    )


def split_address(value: str) -> tuple[str, str]:
    """(display name, lowercased address) from a header value as mail clients
    write it in a forwarded block: `Name <a@b>`, `Name [mailto:a@b]`, `a@b`."""
    value = (value or "").strip()[:HEADER_VALUE_MAX]
    match = (
        _ANGLE_ADDRESS.search(value)
        or _MAILTO_ADDRESS.search(value)
        or ADDRESS.search(value)
    )
    if not match:
        return "", ""
    address = (match.group(1) if match.groups() else match.group(0)).strip(".")
    name = (value[: match.start()] + value[match.end() :]).strip(" \"'*<>[]()")
    return " ".join(name.split()), address.lower()
