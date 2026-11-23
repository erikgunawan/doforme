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
        if (Path(policy['receipts']) / 'denied').exists():
            raise ValueError('A previous denial stopped this worker')
        call = event['toolCall']
        canonical = guard_call(call['name'], call['args'], policy['repo'], policy['skills'], policy)
        decision = 'allow'
    except (ValueError, KeyError, TypeError, OSError, AttributeError):
        canonical = None
        try:
            descriptor = os.open(Path(policy['receipts']) / 'denied', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
        except (ValueError, KeyError, TypeError, OSError, UnboundLocalError):
            pass
    try:
        receipt = {'step': event.get('stepIdx'), 'call': canonical, 'decision': decision}
        write_json(Path(policy['receipts']) / ('guard-' + str(uuid.uuid4()) + '.json'), receipt)
    except (ValueError, KeyError, TypeError, OSError, UnboundLocalError):
        decision = 'deny'
    print(json.dumps({'decision': decision}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
