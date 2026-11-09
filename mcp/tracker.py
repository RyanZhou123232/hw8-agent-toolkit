"""Narrow XLSX adapter: patch status/notes XML and preserve other ZIP members."""

from contextlib import contextmanager
from datetime import datetime, timedelta
from hashlib import sha256
from io import BytesIO
import os
from pathlib import Path
import posixpath
import re
import shutil
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from zipfile import ZipFile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
HEADERS = {"D5": "Company", "E5": "link", "F5": "Title", "G5": "App day",
           "L5": "status", "M5": "other info"}


def cell_text(cell, strings):
    if cell is None:
        return ""
    if cell.find("s:f", NS) is not None:
        raise ValueError("Formula in a tracker data cell is not supported.")
    if cell.get("t") == "inlineStr":
        return "".join(cell.itertext())
    value = cell.find("s:v", NS)
    text = (value.text or "") if value is not None else ""
    return strings[int(text)] if cell.get("t") == "s" else text


class Tracker:
    def __init__(self, path, sheet="Sheet1"):
        self.path = Path(path).expanduser().resolve()
        if self.path.suffix.lower() != ".xlsx":
            raise ValueError("Only .xlsx workbooks are supported.")
        if self.path.name == "公司账号.xlsx":
            raise ValueError("The company-account workbook is outside this tool's scope.")
        self.sheet = sheet

    def _read(self):
        raw = self.path.read_bytes()
        with ZipFile(BytesIO(raw)) as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheets = workbook.findall("s:sheets/s:sheet", NS)
            sheet = next((s for s in sheets if s.get("name") == self.sheet), None)
            if sheet is None:
                raise ValueError(f"Worksheet not found: {self.sheet}")
            rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            target = next(r.get("Target") for r in rels if r.get("Id") == sheet.get(f"{{{REL}}}id"))
            member = target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
            xml = archive.read(member)
            tree = ET.fromstring(xml)
            if tree.find("s:sheetProtection", NS) is not None:
                raise ValueError("Protected worksheets are not supported.")
            strings = []
            if "xl/sharedStrings.xml" in archive.namelist():
                strings = ["".join(si.itertext()) for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
            cells = {c.get("r"): c for c in tree.findall("s:sheetData/s:row/s:c", NS)}
            for address, expected in HEADERS.items():
                if cell_text(cells.get(address), strings) != expected:
                    raise ValueError(f"Unexpected schema at {address}; expected {expected!r}.")
            records = []
            for r in tree.findall("s:sheetData/s:row", NS):
                number = int(r.get("r"))
                if number < 6:
                    continue
                fields = {key: cell_text(cells.get(f"{col}{number}"), strings) for col, key in
                          [("D", "company"), ("E", "link"), ("F", "title"), ("G", "applied_date"),
                           ("L", "status"), ("M", "notes"), ("Q", "application_link")]}
                if not fields["company"]:
                    continue
                date = fields["applied_date"]
                if date and re.fullmatch(r"\d+(?:\.\d+)?", date):
                    props = workbook.find("s:workbookPr", NS)
                    epoch = datetime(1904, 1, 1) if props is not None and props.get("date1904") in ("1", "true") else datetime(1899, 12, 30)
                    fields["applied_date"] = (epoch + timedelta(days=float(date))).date().isoformat()
                records.append({"row": number, **fields})
        return raw, member, xml, records

    def query(self, company="", title="", status_filter="", limit=20):
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100.")
        raw, _, _, records = self._read()
        matches = [r for r in records if all(q.casefold() in r[k].casefold() for k, q in
                   [("company", company), ("title", title), ("status", status_filter)])]
        return {"version": sha256(raw).hexdigest(), "sheet": self.sheet,
                "total": len(matches), "records": matches[:limit], "truncated": len(matches) > limit}

    @contextmanager
    def _lock(self):
        # Cooperative lock across MCP processes. Other writers do not use it.
        lock = self.path.with_name(self.path.name + ".mcp-lock")
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError("Another MCP update is in progress; retry later.") from None
        try:
            os.close(fd)
            if self.path.with_name("~$" + self.path.name).exists():
                raise ValueError("Workbook is open in Excel. Close it before updating.")
            yield
        finally:
            lock.unlink(missing_ok=True)

    def update(self, row, version, new_status=None, new_notes=None):
        if not isinstance(row, int) or isinstance(row, bool) or not version:
            raise ValueError("Query first; update requires row and version.")
        changes = {k: v for k, v in {"status": new_status, "notes": new_notes}.items() if v is not None}
        if not changes:
            raise ValueError("Supply new_status and/or new_notes.")
        for key, value in changes.items():
            if not isinstance(value, str) or len(value) > 2000 or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]", value):
                raise ValueError("Text must be valid XML text, at most 2000 characters.")
            if key == "status" and not value.strip():
                raise ValueError("Status must not be blank.")
        with self._lock():
            raw, member, xml, records = self._read()
            if sha256(raw).hexdigest() != version:
                raise ValueError("Stale workbook version. Query again before updating.")
            record = next((r for r in records if r["row"] == row), None)
            if record is None:
                raise ValueError("No application record exists at this row.")
            delta = {k: {"before": record[k], "after": v} for k, v in changes.items() if record[k] != v}
            if not delta:
                return {"updated": False, "row": row, "version": version, "changes": {}}
            updated_xml = xml
            for key, values in delta.items():
                col = "L" if key == "status" else "M"
                address = f"{col}{row}".encode()
                # Stop at the first complete cell; a greedy attribute scan can
                # swallow a self-closing cell's slash and consume its neighbor.
                pattern = rb'<c\b(?=[^>]*\br="' + address + rb'")[^>]*?(?:/>|>.*?</c>)'
                match = re.search(pattern, updated_xml, re.DOTALL)
                old = match.group() if match else b'<c r="' + address + b'"/>'
                if b"<f" in old:
                    raise ValueError("Refusing to replace a formula.")
                attrs = old[2:old.index(b">")].rstrip(b"/")
                attrs = re.sub(rb'\s+t="[^"]*"', b"", attrs)
                text = escape(values["after"]).replace("\r", "&#13;").encode("utf-8")
                replacement = b'<c' + attrs + b' t="inlineStr"><is><t xml:space="preserve">' + text + b'</t></is></c>'
                if match:
                    updated_xml = updated_xml[:match.start()] + replacement + updated_xml[match.end():]
                else:
                    row_pattern = rb'<row\b(?=[^>]*\br="' + str(row).encode() + rb'")[^>]*>.*?</row>'
                    row_match = re.search(row_pattern, updated_xml, re.DOTALL)
                    if row_match is None:
                        raise ValueError("Unsupported worksheet XML layout.")
                    row_xml = row_match.group()
                    # L and M are single-letter columns; insert before the next column.
                    following = next((c for c in re.finditer(rb'<c\b[^>]*\br="([A-Z]+)\d+"', row_xml)
                                      if (len(c.group(1)), c.group(1)) > (1, col.encode())), None)
                    offset = following.start() if following else row_xml.index(b"</row>")
                    position = row_match.start() + offset
                    updated_xml = updated_xml[:position] + replacement + updated_xml[position:]
            ET.fromstring(updated_xml)
            buffer = BytesIO()
            with ZipFile(BytesIO(raw)) as source, ZipFile(buffer, "w") as dest:
                dest.comment = source.comment
                for info in source.infolist():
                    dest.writestr(info, updated_xml if info.filename == member else source.read(info.filename))
            output = buffer.getvalue()
            backups = self.path.parent / ".application-tracker-backups"
            backups.mkdir(exist_ok=True)
            backup = backups / f"{self.path.stem}-{datetime.now():%Y%m%d-%H%M%S-%f}.xlsx"
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(dir=self.path.parent, suffix=".xlsx", delete=False) as temp:
                    temp_path = Path(temp.name)
                    temp.write(output)
                    temp.flush()
                    os.fsync(temp.fileno())
                if sha256(self.path.read_bytes()).hexdigest() != version:
                    raise ValueError("Workbook changed during update. Query again.")
                backup.write_bytes(raw)
                shutil.copymode(self.path, temp_path)
                os.replace(temp_path, self.path)
            finally:
                if temp_path is not None:
                    temp_path.unlink(missing_ok=True)
            return {"updated": True, "row": row, "company": record["company"], "title": record["title"],
                    "changes": delta, "version": sha256(output).hexdigest(), "backup": str(backup)}
