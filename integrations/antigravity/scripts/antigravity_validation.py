"""Minimal stdio MCP command broker. No worker marker means no execution."""
import json
import os
from pathlib import Path
import signal
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine/scripts'))
from antigravity_commands import execute, VALIDATION_TOOL as TOOL


def dispatch(request):
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
        raise ValueError('Invalid JSON-RPC request')
    method, params = request.get('method'), request.get('params', {})
    if method == 'initialize':
        version = params.get('protocolVersion')
        if version not in ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25'):
            version = '2024-11-05'
        return {'protocolVersion': version, 'capabilities': {'tools': {}},
                'serverInfo': {'name': 'doforme-validation', 'version': '1.0.0'}}
    if method == 'ping':
        return {}
    if method == 'tools/list':
        return {'tools': [TOOL]}
    if method == 'tools/call':
        try:
            args = params.get('arguments')
            if params.get('name') != 'run' or not isinstance(args, dict) or set(args) != {'command_index'}:
                raise ValueError('Only the exact reviewed command-index tool is available')
            marker = os.environ.get('DOFORME_AGY_GUARD')
            if marker is None:
                raise ValueError('Execution requires an explicitly authorized doforme worker')
            record = execute(json.loads(marker), args['command_index'])
            return {'content': [{'type': 'text', 'text': json.dumps(record)},
                                {'type': 'text', 'text': 'doforme-command-receipt:' + record['receipt_id']}],
                    'isError': False}
        except (ValueError, OSError, KeyError, TypeError) as error:
            return {'content': [{'type': 'text', 'text': str(error)}], 'isError': True}
    if isinstance(method, str) and method.startswith('notifications/'):
        return None
    raise ValueError('Unsupported MCP method')


def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    while True:
        line = sys.stdin.readline(200001)
        if not line:
            break
        request = None
        try:
            if len(line) > 200000:
                raise ValueError('MCP input exceeds the bounded message size')
            request = json.loads(line)
            result = dispatch(request)
            if isinstance(request, dict) and 'id' in request:
                print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)
        except (ValueError, TypeError, AttributeError) as error:
            ident = request.get('id') if isinstance(request, dict) else None
            print(json.dumps({'jsonrpc': '2.0', 'id': ident,
                              'error': {'code': -32602, 'message': str(error)}}), flush=True)


if __name__ == '__main__':
    main()
