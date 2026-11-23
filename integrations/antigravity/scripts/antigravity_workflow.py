"""Native Antigravity entry point: read-only target, private report writes only."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine/scripts'))
import guided_workflow as G
from antigravity_runtime import runtime_identity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('doctor', 'status', 'issues', 'prepare', 'analyze', 'plan'))
    p.add_argument('--repo', required=True)
    p.add_argument('--issue')
    p.add_argument('--data-json')
    p.add_argument('--confirm')
    p.add_argument('--storage')
    p.add_argument('--new', action='store_true')
    p.add_argument('--retry', action='store_true')
    p.add_argument('--source', choices=('auto', 'github', 'local'), default='auto')
    a = p.parse_args()
    try:
        repo = G.repository_root(a.repo)
        if a.action == 'doctor':
            result = G.repo_doctor(repo)
            result['findings'] = [item for item in result['findings'] if item['check'] != 'test_commands']
            for item in result['findings']:
                if item['check'] == 'profile':
                    item['message'] = 'No reviewed profile; supply existing requirement paths during analysis preparation'
            result['next_action'] = 'Choose an issue and existing owner-confirmed requirement sources'
            try:
                result['runtime'] = runtime_identity()
            except (ValueError, OSError) as error:
                result['findings'].append({'check': 'antigravity', 'message': str(error)})
            result['supported_stages'] = ['analyze', 'plan']
        elif a.action == 'status':
            result = G.show(repo, a.issue, a.storage) if a.issue else G.list_sessions(repo, a.storage)
        elif a.action == 'issues':
            result = G.list_issues(repo, a.source)
        elif a.action == 'prepare':
            if not a.issue:
                raise ValueError('Choose an explicit issue before preparing analysis')
            if a.data_json and len(a.data_json) > 150000:
                raise ValueError('Preparation JSON exceeds size limit')
            data = G.proposal_json(a.data_json or '{}')
            if any(data.get(key) for key in ('edit_paths', 'test_commands', 'artifact_paths')):
                raise ValueError('Antigravity preparation cannot request edits, tests or artifacts')
            result = G.prepare(repo, a.issue, data, a.confirm, a.storage, a.new)
        else:
            if not a.issue:
                raise ValueError('Choose an explicit issue before analysis/planning')
            result = G.run(repo, a.issue, a.action, a.confirm, a.storage, a.retry, runtime='antigravity')
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'needs_attention', 'message': str(error),
                          'execution': 'not_established', 'next_action': 'Explain the missing prerequisite; never widen permissions or retry silently'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
