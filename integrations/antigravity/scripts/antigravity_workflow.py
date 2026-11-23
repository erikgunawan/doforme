"""Native Antigravity entry point: reviewed setup and private workflow reports."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine/scripts'))
import guided_workflow as G
from init_repo import initialize
from antigravity_runtime import runtime_identity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('init', 'setup', 'doctor', 'status', 'issues', 'prepare', 'scope', *G.ORDER, 'endtoend'))
    p.add_argument('--repo', required=True)
    p.add_argument('--issue')
    p.add_argument('--data-json')
    p.add_argument('--confirm')
    p.add_argument('--storage')
    p.add_argument('--new', action='store_true')
    p.add_argument('--retry', action='store_true')
    p.add_argument('--source', choices=('auto', 'github', 'local'), default='auto')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--inspect', action='store_true')
    a = p.parse_args()
    try:
        repo = G.repository_root(a.repo)
        if a.data_json and len(a.data_json) > 150000:
            raise ValueError('Proposal JSON exceeds size limit')
        if (a.write or a.inspect) and (a.action != 'init' or a.data_json or a.confirm):
            raise ValueError('--write/--inspect only apply to explicit draft init, without setup data or confirmation')
        if a.action == 'init':
            result = initialize(repo, write=a.write) if a.write or a.inspect else G.discover(repo)
        elif a.action == 'setup':
            result = G.setup(repo, G.proposal_json(a.data_json or '{}'), a.confirm)
        elif a.action == 'doctor':
            result = G.repo_doctor(repo)
            try:
                result['runtime'] = runtime_identity()
            except (ValueError, OSError) as error:
                result['findings'].append({'check': 'antigravity', 'message': str(error)})
            result['supported_stages'] = list(G.ORDER)
        elif a.action == 'status':
            result = G.show(repo, a.issue, a.storage) if a.issue else G.list_sessions(repo, a.storage)
        elif a.action == 'issues':
            result = G.list_issues(repo, a.source)
        elif a.action in ('prepare', 'scope'):
            if not a.issue:
                raise ValueError('Choose an explicit issue before preparing analysis')
            if a.data_json and len(a.data_json) > 150000:
                raise ValueError('Preparation JSON exceeds size limit')
            data = G.proposal_json(a.data_json or '{}')
            if a.action == 'scope':
                result = G.scope(repo, a.issue, data, a.confirm, a.storage)
            else:
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
