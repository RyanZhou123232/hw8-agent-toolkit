"""Explicit command-line MCP client for agents whose native registration is unavailable.

The config registers a stdio server (command, args, env). List the actual tool
catalog first; call a discovered tool with JSON arguments on stdin. This is a
CLI adapter, not native Codex MCP registration. Python 3.10+, standard library.
"""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def public_result(result):
    result = json.loads(json.dumps(result))
    for block in result.get('content', []):
        if block.get('type') != 'text':
            continue
        try:
            value = json.loads(block['text'])
        except (ValueError, KeyError):
            continue
        if isinstance(value, dict) and 'records' in value:
            value['records'] = [{k: r.get(k) for k in ('row', 'company', 'title', 'status', 'applied_date')} for r in value['records']]
            value['private_links_and_notes_omitted'] = True
            block['text'] = json.dumps(value, ensure_ascii=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--evidence', help='Optional sanitized protocol record path')
    parser.add_argument('operation', choices=('list', 'call', 'skills', 'skill'))
    parser.add_argument('tool', nargs='?')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    if args.operation in ('skills', 'skill'):
        catalog = []
        for directory in config.get('skills_directories', []):
            for path in sorted(Path(directory).glob('*/SKILL.md')):
                text = path.read_text(encoding='utf-8')
                if not text.startswith('---\n'):
                    continue
                frontmatter = text.split('---', 2)[1]
                name = re.search(r'^name:\s*(.+)$', frontmatter, re.M)
                description = re.search(r'^description:\s*(.+)$', frontmatter, re.M)
                if name and description:
                    catalog.append({'name': name.group(1), 'description': description.group(1), 'path': str(path.resolve())})
        if args.operation == 'skills':
            print(json.dumps({'skills': catalog}, ensure_ascii=True, indent=2))
            return 0
        selected = [item for item in catalog if item['name'] == args.tool]
        if len(selected) != 1:
            parser.error('skill requires one uniquely named discovered skill')
        print(json.dumps({'name': args.tool, 'instructions': Path(selected[0]['path']).read_text(encoding='utf-8')}, ensure_ascii=True, indent=2))
        return 0
    requests = [
        {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 'hw8-agent-cli', 'version': '1.0'}}},
        {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
        {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
    ]
    if args.operation == 'call':
        if not args.tool:
            parser.error('call requires a discovered tool name')
        arguments = json.load(sys.stdin)
        requests.append({'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': args.tool, 'arguments': arguments}})
    env = {**os.environ, **config.get('env', {})}
    workbook = Path(env['APPLICATION_TRACKER_PATH']) if 'APPLICATION_TRACKER_PATH' in env else None
    before = sha256(workbook.read_bytes()).hexdigest() if workbook else None
    wire = ''.join(json.dumps(r) + '\n' for r in requests).encode()
    started = datetime.now(timezone.utc).isoformat()
    process = subprocess.run([config['command'], *config.get('args', [])], env=env, input=wire, capture_output=True, timeout=20)
    if process.returncode:
        raise RuntimeError(f'MCP process exited {process.returncode}: {process.stderr.decode(errors="replace")}')
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    expected_ids = [r['id'] for r in requests if 'id' in r]
    if [r.get('id') for r in responses] != expected_ids:
        raise RuntimeError('MCP reply IDs do not match requests')
    if any('error' in r for r in responses):
        raise RuntimeError(json.dumps(responses))
    record = {'recorded_utc': started, 'client': 'Codex Work agent using explicit hw8-agent-cli stdio adapter; not native Codex registration',
              'requests': requests, 'responses': [{**r, 'result': public_result(r['result'])} for r in responses],
              'source_sha256_before': before, 'source_sha256_after': sha256(workbook.read_bytes()).hexdigest() if workbook else None}
    if args.evidence:
        target = Path(args.evidence)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    result = record['responses'][-1]['result']
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result.get('isError') else 0


if __name__ == '__main__':
    sys.exit(main())
