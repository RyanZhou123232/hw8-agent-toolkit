"""Synthetic data only. Run: python -m unittest discover -s mcp -v"""

from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from tracker import HEADERS, Tracker

ROOT = Path(__file__).resolve().parent


def fixture(path):
    def cell(address, text):
        return f'<c r="{address}" s="0" t="inlineStr"><is><t>{text}</t></is></c>'
    # Fixture values come from the workbook contract, not implementation HEADERS.
    expected_headers = {"D5": "Company", "E5": "link", "F5": "Title",
                        "G5": "App day", "L5": "status", "M5": "other info"}
    header = ''.join(cell(k, v) for k, v in expected_headers.items())
    rows = []
    for row, company, title in [(6, 'Example Co', 'Data Intern'), (7, 'Example Co', 'SWE Intern'), (8, 'Other Co', 'Analyst')]:
        cells = cell(f'D{row}', company) + cell(f'E{row}', f'https://example.com/job/{row}') + cell(f'F{row}', title)
        cells += f'<c r="G{row}"><v>46333</v></c>'
        cells += cell(f'L{row}', 'Applied')
        # Test rich existing notes, an absent notes cell, and a self-closing cell.
        cells += cell(f'M{row}', 'Original note') if row == 6 else '' if row == 7 else f'<c r="M{row}" s="0"/>'
        cells += cell(f'Q{row}', f'https://example.com/application/{row}')
        rows.append(f'<row r="{row}">{cells}</row>')
    xml = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           '<dimension ref="D5:Q8"/><sheetData><row r="5">' + header + '</row>' + ''.join(rows) + '</sheetData></worksheet>')
    with ZipFile(path, 'w', ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml', xml)
        z.writestr('unrelated/preserved.bin', b'\x00\x01DO NOT CHANGE\xff')


class TrackerTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT.parent / '.local-tests'
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'applications.xlsx'
        fixture(self.path)
        self.tracker = Tracker(self.path)

    def test_query_filters_duplicates_empty_results_and_limit(self):
        q = self.tracker.query(company='EXAMPLE', limit=1)
        self.assertEqual(q['total'], 2)
        self.assertTrue(q['truncated'])
        self.assertEqual(self.tracker.query(company='Example', title='swe')['records'][0]['row'], 7)
        self.assertEqual(self.tracker.query(company='missing')['records'], [])
        self.assertEqual(self.tracker.query()['records'][0]['applied_date'], '2026-11-07')
        with self.assertRaises(ValueError):
            self.tracker.query(limit=0)

    def test_update_roundtrip_backup_and_preserve_other_parts(self):
        before = self.path.read_bytes()
        query = self.tracker.query()
        notes = '=not a formula <tag> & 中文\nnext\rline'
        result = self.tracker.update(6, query['version'], 'Interview', notes)
        self.assertTrue(result['updated'])
        self.assertEqual(Path(result['backup']).read_bytes(), before)
        after = self.path.read_bytes()
        with ZipFile(BytesIO(before)) as old, ZipFile(BytesIO(after)) as new:
            self.assertEqual(old.namelist(), new.namelist())
            for member in old.namelist():
                if member == 'xl/worksheets/sheet1.xml':
                    scrub = lambda x: re.sub(rb'<c\b(?=[^>]*\br="[LM]6")[^>]*(?:/>|>.*?</c>)', b'EDITED', x, flags=re.DOTALL)
                    self.assertEqual(scrub(old.read(member)), scrub(new.read(member)))
                else:
                    self.assertEqual(old.read(member), new.read(member))
        record = self.tracker.query()['records'][0]
        self.assertEqual(record['status'], 'Interview')
        self.assertEqual(record['notes'], notes)
        self.assertEqual(self.tracker.query()['records'][1]['status'], 'Applied')
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.tracker.update(6, query['version'], 'Rejected')
        self.assertEqual(self.path.read_bytes(), after)

    def test_sparse_and_self_closing_cells(self):
        for row in (7, 8):
            q = self.tracker.query()
            self.tracker.update(row, q['version'], new_notes='new note')
            self.assertEqual(next(r for r in self.tracker.query()['records'] if r['row'] == row)['notes'], 'new note')
        q = self.tracker.query()
        self.tracker.update(7, q['version'], new_notes='')
        self.assertEqual(self.tracker.query(title='SWE')['records'][0]['notes'], '')

    def test_rejections_and_noop_leave_file_unchanged(self):
        raw = self.path.read_bytes()
        version = self.tracker.query()['version']
        for args in [(None, version, 'Interview'), (99, version, 'Interview'), (6, None, 'Interview'),
                     (6, version, ''), (6, version, 'bad\x00text'), (6, version, None), (6, version, 123)]:
            with self.assertRaises(ValueError):
                self.tracker.update(*args)
            self.assertEqual(self.path.read_bytes(), raw)
        self.assertFalse(self.tracker.update(6, version, 'Applied')['updated'])
        self.assertFalse((self.path.parent / '.application-tracker-backups').exists())

    def test_self_closing_targets_preserve_following_cells(self):
        def without_target(xml, address):
            start = xml.index(f'<c r="{address}"'.encode())
            opening_end = xml.index(b'>', start) + 1
            end = opening_end if xml[opening_end - 2:opening_end] == b'/>' else xml.index(b'</c>', opening_end) + 4
            return xml[:start] + b'EDITED' + xml[end:]

        for address, row, changes, preserved_field in [
            ('M8', 8, {'new_notes': 'new note'}, 'application_link'),
            ('L6', 6, {'new_status': 'Interview'}, 'notes'),
        ]:
            with self.subTest(address=address):
                fixture(self.path)
                if address == 'L6':
                    raw = self.path.read_bytes()
                    with ZipFile(BytesIO(raw)) as source, ZipFile(self.path, 'w') as dest:
                        for info in source.infolist():
                            content = source.read(info.filename)
                            if info.filename == 'xl/worksheets/sheet1.xml':
                                content = content.replace(b'<c r="L6" s="0" t="inlineStr"><is><t>Applied</t></is></c>', b'<c r="L6" s="0"/>')
                            dest.writestr(info, content)
                before = self.path.read_bytes()
                query = self.tracker.query()
                previous = next(r for r in query['records'] if r['row'] == row)
                result = self.tracker.update(row, query['version'], **changes)
                current = next(r for r in self.tracker.query()['records'] if r['row'] == row)
                self.assertEqual(current[preserved_field], previous[preserved_field])
                self.assertEqual(Path(result['backup']).read_bytes(), before)
                with ZipFile(BytesIO(before)) as old, ZipFile(self.path) as new:
                    for member in old.namelist():
                        if member == 'xl/worksheets/sheet1.xml':
                            self.assertEqual(without_target(old.read(member), address), without_target(new.read(member), address))
                        else:
                            self.assertEqual(old.read(member), new.read(member))

    def test_excel_and_mcp_locks(self):
        version = self.tracker.query()['version']
        for name in ('~$applications.xlsx', 'applications.xlsx.mcp-lock'):
            marker = self.path.parent / name
            marker.touch()
            with self.assertRaises(ValueError):
                self.tracker.update(6, version, 'Interview')
            self.assertEqual(sha256(self.path.read_bytes()).hexdigest(), version)
            marker.unlink()

    def test_wrong_schema_and_accounts_workbook_rejected(self):
        with self.assertRaises(ValueError):
            Tracker(self.path.parent / '公司账号.xlsx')
        with self.assertRaises(ValueError):
            Tracker(self.path, 'NoSuchSheet').query()
        raw = self.path.read_bytes()
        with ZipFile(BytesIO(raw)) as source, ZipFile(self.path, 'w') as dest:
            for info in source.infolist():
                dest.writestr(info, source.read(info.filename).replace(b'>Company<', b'>Wrong<'))
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.tracker.query()

    def test_stdio_real_subprocess_handshake_query_update_errors(self):
        version = sha256(self.path.read_bytes()).hexdigest()
        requests = [
            {'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'smoke-test', 'version': '1'}}},
            {'method': 'notifications/initialized'},
            {'id': 2, 'method': 'tools/list'},
            {'id': 3, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'query', 'company': 'Example'}}},
            {'id': 4, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'update', 'row': 7, 'version': version, 'new_status': 'Interview', 'new_notes': 'Synthetic test only'}}},
            {'id': 5, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'query', 'title': 'SWE'}}},
            {'id': 6, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'update', 'row': 7, 'version': version, 'new_status': 'Rejected'}}},
            {'id': 7, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'delete'}}},
            {'id': 8, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'query', 'limit': True}}},
            {'id': 9, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'update', 'row': 6, 'version': version, 'company': 'Other', 'new_status': 'Applied'}}},
            {'id': 10, 'method': 'tools/call', 'params': {'name': 'application_tracker', 'arguments': {'action': 'query', 'file': '公司账号.xlsx'}}},
            {'id': 11, 'method': 'ping'},
        ]
        wire = '\n'.join(json.dumps({'jsonrpc': '2.0', **r}) for r in requests) + '\n'
        env = {**os.environ, 'APPLICATION_TRACKER_PATH': str(self.path), 'APPLICATION_TRACKER_SHEET': 'Sheet1'}
        process = subprocess.run([sys.executable, str(ROOT / 'server.py')], input=wire.encode(), capture_output=True, env=env, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        replies = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([r['id'] for r in replies], list(range(1, 12)))
        self.assertEqual(replies[0]['result']['protocolVersion'], '2025-06-18')
        self.assertEqual(len(replies[1]['result']['tools']), 1)
        unpack = lambda reply: json.loads(reply['result']['content'][0]['text'])
        self.assertEqual(unpack(replies[2])['total'], 2)
        self.assertTrue(unpack(replies[3])['updated'])
        self.assertEqual(unpack(replies[4])['records'][0]['status'], 'Interview')
        for reply in replies[5:10]:
            self.assertTrue(reply['result']['isError'])
        self.assertEqual(replies[10]['result'], {})


if __name__ == '__main__':
    unittest.main()
