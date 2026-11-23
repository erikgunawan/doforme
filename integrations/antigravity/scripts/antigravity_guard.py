"""PreToolUse gate for explicitly marked doforme worker children only."""
import json
import os
from pathlib import Path
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine/scripts'))
from antigravity_runtime import guard_call
from workflow_state import write_json


def main():
    marker = os.environ.get('DOFORME_AGY_GUARD')
    if marker is None:
        print('{"decision":"allow"}')
        return 0
    decision = 'deny'
    try:
        policy = json.loads(marker)
        raw = sys.stdin.read(150001)
        if len(raw) > 150000:
            raise ValueError('Oversized hook input')
        event = json.loads(raw)
        call = event['toolCall']
        canonical = guard_call(call['name'], call['args'], policy['repo'], policy['skills'])
        decision = 'allow'
    except (ValueError, KeyError, TypeError, OSError, AttributeError):
        canonical = None
    try:
        receipt = {'step': event.get('stepIdx'), 'call': canonical, 'decision': decision}
        write_json(Path(policy['receipts']) / (str(uuid.uuid4()) + '.json'), receipt)
    except (ValueError, KeyError, TypeError, OSError, UnboundLocalError):
        decision = 'deny'
    print(json.dumps({'decision': decision}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
