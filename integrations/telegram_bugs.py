"""Standalone GitHub bug notifications with explicit owner-attested resolution."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 1_000_000
DECLARATION = re.compile(r'\A```doforme-resolution\s*\n(.*?)\n```\Z', re.S)


def checked_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON field')
            result[key] = value
        return result
    return json.loads(text, object_pairs_hook=unique)


def read_json(path):
    path = Path(path).absolute()
    if any(item.is_symlink() for item in (path, *path.parents)):
        raise ValueError('Notification input must not contain symlinks')
    if not stat.S_ISREG(path.stat().st_mode) or path.stat().st_size > MAX_BYTES:
        raise ValueError('Notification input must be a bounded regular file')
    return checked_json(path.read_text(encoding='utf-8'))


def write_private(path, data):
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def positive(value):
    return type(value) is int and value > 0


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing GitHub timestamp')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Timestamp requires timezone')
    return result


def repo_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', value) or any(
            item in ('.', '..') for item in value.split('/')):
        raise ValueError('Select one GitHub owner/repository')
    return value


class GitHub:
    def get(self, endpoint):
        result = subprocess.run(['gh', 'api', '--hostname', 'github.com', '--method', 'GET', endpoint],
                                capture_output=True, timeout=30)
        if result.returncode or len(result.stdout) > MAX_BYTES:
            raise ValueError('GitHub metadata unavailable or oversized')
        return checked_json(result.stdout.decode('utf-8'))

    def pages(self, endpoint):
        records = []
        for page in range(1, 11):
            separator = '&' if '?' in endpoint else '?'
            data = self.get(endpoint + separator + f'per_page=100&page={page}')
            if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
                raise ValueError('Malformed GitHub metadata list')
            records.extend(data)
            if len(data) < 100:
                return records
        raise ValueError('Metadata exceeds pagination bound; manual review required')


def approvers(value):
    names = {item.lower() for item in re.split(r'[\s,]+', value.strip()) if item}
    if not names or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,38})', item) for item in names):
        raise ValueError('Configure explicit GitHub resolution approvers')
    return names


def latest_close(client, repository, number, issue):
    timeline = client.pages(f'repos/{repository}/issues/{number}/timeline')
    transitions = []
    for row in timeline:
        if row.get('event') in ('closed', 'reopened'):
            if not positive(row.get('id')):
                raise ValueError('Missing immutable issue transition ID')
            transitions.append((timestamp(row.get('created_at')), row['id'], row['event']))
    transitions.sort()
    if not transitions or transitions[-1][2] != 'closed' or transitions[-1][0] != timestamp(issue.get('closed_at')):
        raise ValueError('Current closure and issue timeline disagree')
    reopened = max((date for date, _, event in transitions if event == 'reopened'), default=None)
    return transitions[-1][1], reopened


def declared_resolution(client, repository, number, issue, owners, required_checks):
    close_id, reopened = latest_close(client, repository, number, issue)
    comments = client.pages(f'repos/{repository}/issues/{number}/comments')
    comments.sort(key=lambda row: (timestamp(row.get('created_at')), row.get('id', 0)), reverse=True)
    selected = None
    for comment in comments:
        login = comment.get('user', {}).get('login', '')
        if not isinstance(login, str) or login.lower() not in owners:
            continue
        match = DECLARATION.fullmatch(str(comment.get('body', '')).strip())
        if not match:
            continue
        created = timestamp(comment.get('created_at'))
        if reopened is not None and created <= reopened:
            continue
        # Old edited approvals are not silently reused. Submit a new declaration.
        if comment.get('created_at') != comment.get('updated_at'):
            raise ValueError('Resolution declaration was edited; submit a new owner comment')
        selected = comment, checked_json(match.group(1))
        break
    if selected is None:
        raise ValueError('No current unedited resolution declaration from a configured approver')
    comment, declaration = selected
    fields = {'issue', 'pr', 'merge_commit', 'qa', 'business_acceptance', 'evidence_url', 'source_refs'}
    if not isinstance(declaration, dict) or set(declaration) != fields:
        raise ValueError('Resolution declaration fields missing or unknown')
    if declaration['issue'] != number or type(declaration['issue']) is not int or not positive(declaration['pr']):
        raise ValueError('Resolution issue/PR mismatch')
    if declaration['qa'] != 'passed' or declaration['business_acceptance'] != 'accepted':
        raise ValueError('Owner has not declared QA and business acceptance passed')
    sha = declaration['merge_commit']
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Resolution requires an exact merge commit SHA')
    refs = declaration['source_refs']
    if not isinstance(refs, list) or not refs or len(refs) > 30 or any(
            not isinstance(ref, str) or not ref.strip() or len(ref) > 500 for ref in refs):
        raise ValueError('Owner must name applicable source/AC references')
    pr = client.get(f'repos/{repository}/pulls/{declaration["pr"]}')
    metadata = client.get(f'repos/{repository}')
    if (pr.get('merged') is not True or pr.get('merge_commit_sha') != sha or
            pr.get('base', {}).get('repo', {}).get('full_name', '').lower() != repository.lower() or
            pr.get('base', {}).get('ref') != metadata.get('default_branch')):
        raise ValueError('Declared PR is not merged into this repository default branch at the declared SHA')
    merged = timestamp(pr.get('merged_at'))
    if timestamp(comment.get('created_at')) < merged:
        raise ValueError('Acceptance declaration predates PR merge')
    evidence_url = declaration['evidence_url']
    pattern = re.escape(f'https://github.com/{repository}/issues/{number}#issuecomment-') + r'([1-9][0-9]*)'
    match = re.fullmatch(pattern, evidence_url) if isinstance(evidence_url, str) else None
    if match is None:
        raise ValueError('Evidence must link to a QA/UAT comment on this same issue')
    evidence = client.get(f'repos/{repository}/issues/comments/{match.group(1)}')
    if (evidence.get('html_url') != evidence_url or
            evidence.get('user', {}).get('login', '').lower() not in owners or
            evidence.get('created_at') != evidence.get('updated_at') or
            timestamp(evidence.get('created_at')) < merged or
            reopened is not None and timestamp(evidence.get('created_at')) <= reopened or
            sha not in str(evidence.get('body', '')) or not str(evidence.get('body', '')).strip()):
        raise ValueError('QA/UAT evidence must be a current unedited approver comment naming the merge SHA')
    if not required_checks:
        raise ValueError('Configure required GitHub Actions check names before resolved notifications')
    checks = client.get(f'repos/{repository}/commits/{sha}/check-runs?per_page=100')
    runs = checks.get('check_runs')
    if (not isinstance(runs, list) or type(checks.get('total_count')) is not int or
            checks['total_count'] != len(runs) or any(not isinstance(run, dict) for run in runs)):
        raise ValueError('Required check list is malformed or incomplete')
    latest = {}
    for run in runs:
        if run.get('app', {}).get('slug') == 'github-actions' and run.get('name') in required_checks:
            if not positive(run.get('id')) or run.get('head_sha') != sha:
                raise ValueError('Check identity does not match declared merge SHA')
            old = latest.get(run['name'])
            if old is None or run['id'] > old['id']:
                latest[run['name']] = run
    if any(name not in latest or latest[name].get('status') != 'completed' or
           latest[name].get('conclusion') != 'success' for name in required_checks):
        raise ValueError('Required checks have not succeeded on the merge commit')
    return {'closure_id': close_id, 'declaration_id': comment['id'], 'approver': comment['user']['login'],
            'pr': declaration['pr'], 'merge_commit': sha, 'evidence_url': evidence_url,
            'source_refs': refs, 'business_acceptance': 'owner_attested_accepted'}


def plan(event, repository, event_name, owners='', required_checks=(), bug_label='bug', client=None):
    repository = repo_name(repository)
    if not isinstance(event, dict) or event.get('repository', {}).get('full_name', '').lower() != repository.lower():
        raise ValueError('Event repository differs from trusted runner context')
    payload = event.get('issue', {})
    if 'pull_request' in payload:
        return {'status': 'skipped', 'reason': 'Pull requests are not bug issues'}
    number = event.get('inputs', {}).get('issue_number') if event_name == 'workflow_dispatch' else payload.get('number')
    if event_name == 'workflow_dispatch' and isinstance(number, str) and re.fullmatch(r'[1-9][0-9]*', number):
        number = int(number)
    if not positive(number):
        raise ValueError('Select an explicit positive issue number')
    allowed = {'issues': {'opened', 'labeled', 'closed', 'reopened'}, 'issue_comment': {'created'}}
    if event_name != 'workflow_dispatch' and event.get('action') not in allowed.get(event_name, set()):
        return {'status': 'skipped', 'reason': 'Unsupported issue event'}
    client = client or GitHub()
    issue = client.get(f'repos/{repository}/issues/{number}')
    labels = issue.get('labels')
    url = f'https://github.com/{repository}/issues/{number}'
    if ('pull_request' in issue or issue.get('number') != number or not positive(issue.get('id')) or
            str(issue.get('html_url', '')).lower() != url.lower() or not isinstance(labels, list) or
            any(not isinstance(label, dict) or not isinstance(label.get('name'), str) for label in labels)):
        raise ValueError('Malformed current bug issue identity/labels')
    if bug_label not in {label['name'] for label in labels}:
        return {'status': 'skipped', 'reason': 'Issue does not carry the configured bug label'}
    title = issue.get('title')
    if not isinstance(title, str) or not title.strip() or len(title) > 512:
        raise ValueError('Invalid issue title')
    title = ''.join(char for char in title if char >= ' ' and char != '\x7f')[:250]
    new = event_name == 'issues' and (event.get('action') == 'opened' or
          event.get('action') == 'labeled' and event.get('label', {}).get('name') == bug_label)
    if new and issue.get('state') == 'open':
        return {'status': 'ready', 'topic': 'new', 'key': f'new-{issue["id"]}',
                'repository': repository, 'issue': number,
                'text': f'🐛 Bug baru\n{repository} #{number}\n{title}\n{url}\nStatus: dilaporkan; belum dinyatakan resolved.'}
    if issue.get('state') != 'closed' or issue.get('state_reason') != 'completed':
        return {'status': 'skipped', 'reason': 'Issue is not closed as completed; no resolved claim'}
    try:
        resolution = declared_resolution(client, repository, number, issue, approvers(owners), set(required_checks))
    except ValueError as error:
        return {'status': 'blocked', 'reason': str(error)}
    return {'status': 'ready', 'topic': 'resolved', 'key': f'resolved-{issue["id"]}-{resolution["closure_id"]}',
            'repository': repository, 'issue': number, 'resolution': resolution,
            'text': f'✅ Bug resolved — menurut persetujuan owner\n{repository} #{number}\n{title}\n{url}\n'
                    f'PR: https://github.com/{repository}/pull/{resolution["pr"]}\n'
                    f'Commit: {resolution["merge_commit"]}\nApprover: {resolution["approver"]}\n'
                    f'QA/check wajib: passed; acceptance: owner-attested accepted\nBukti: {resolution["evidence_url"]}'}


def artifact_name(notification):
    return 'doforme-telegram-' + notification['key']


def attempted(client, repository, name):
    data = client.get(f'repos/{repository}/actions/artifacts?name={urllib.parse.quote(name, safe="")}&per_page=100')
    rows = data.get('artifacts')
    if not isinstance(rows, list) or type(data.get('total_count')) is not int or data['total_count'] != len(rows):
        raise ValueError('Receipt artifact metadata unavailable or incomplete')
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get('name'), str) or type(row.get('expired')) is not bool:
            raise ValueError('Malformed receipt artifact')
    return any(row['name'] == name and not row['expired'] for row in rows)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def telegram(token, chat, text):
    if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+', token or '') or not re.fullmatch(r'-?[0-9]+|@[A-Za-z0-9_]{5,}', chat or ''):
        raise ValueError('Configure Telegram token and explicit chat ID in repository secrets')
    if not isinstance(text, str) or not 1 <= len(text) <= 4096:
        raise ValueError('Telegram message exceeds its bound')
    request = urllib.request.Request('https://api.telegram.org/bot' + token + '/sendMessage',
        data=json.dumps({'chat_id': chat, 'text': text, 'link_preview_options': {'is_disabled': True}}).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError()
        result = checked_json(raw.decode('utf-8'))
        if not isinstance(result, dict) or not isinstance(result.get('result'), dict):
            raise ValueError()
        message_id = result['result'].get('message_id')
        if result.get('ok') is not True or not positive(message_id):
            raise ValueError()
        return message_id
    except (ValueError, OSError, urllib.error.URLError):
        raise ValueError('Telegram delivery uncertain; inspect chat and receipt before any manual recovery') from None


def settings():
    return {'repository': os.environ.get('GITHUB_REPOSITORY', ''), 'event_name': os.environ.get('GITHUB_EVENT_NAME', ''),
            'owners': os.environ.get('DOFORME_RESOLUTION_APPROVERS', ''),
            'required_checks': [name.strip() for name in os.environ.get('DOFORME_REQUIRED_CHECKS', '').splitlines() if name.strip()],
            'bug_label': os.environ.get('DOFORME_BUG_LABEL', 'bug')}


def output_lines(values):
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a') as stream:
            for key, value in values.items():
                if not re.fullmatch(r'[a-z_]+', key) or not re.fullmatch(r'[A-Za-z0-9-]+', str(value)):
                    raise ValueError('Unsafe workflow output')
                stream.write(f'{key}={value}\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'send'))
    parser.add_argument('--event', required=True)
    parser.add_argument('--folder', required=True)
    args = parser.parse_args()
    try:
        if os.environ.get('DOFORME_NOTIFY_TELEGRAM') != 'true':
            output_lines({'notify': 'false'})
            print(json.dumps({'status': 'disabled', 'sent': False}))
            return 0
        event = read_json(args.event)
        client = GitHub()
        notification = plan(event, client=client, **settings())
        folder = Path(args.folder).absolute()
        if any(path.is_symlink() for path in (folder, *folder.parents)):
            raise ValueError('Use a non-symlink private notification folder')
        if args.action == 'prepare':
            if notification['status'] != 'ready':
                output_lines({'notify': 'false'})
                print(json.dumps(notification))
                return 0
            name = artifact_name(notification)
            if attempted(client, notification['repository'], name):
                output_lines({'notify': 'false'})
                print(json.dumps({'status': 'already_attempted', 'sent': False}))
                return 0
            folder.mkdir(mode=0o700)
            write_private(folder / 'notification.json', notification)
            write_private(folder / 'attempt.json', {'status': 'attempting', 'key': notification['key'], 'topic': notification['topic']})
            output_lines({'notify': 'true', 'receipt_name': name})
            print(json.dumps({'status': 'prepared', 'topic': notification['topic'], 'sent': False}))
            return 0
        original = read_json(folder / 'notification.json')
        if folder.stat().st_mode & 0o077 or notification != original:
            raise ValueError('Notification state/approval changed before sending; no message sent')
        if not attempted(client, original['repository'], artifact_name(original)):
            raise ValueError('Durable pre-send receipt is missing; no message sent')
        write_private(folder / 'delivery.json', {'status': 'attempting', 'sent': False})
        message_id = telegram(os.environ.get('TELEGRAM_BOT_TOKEN'), os.environ.get('TELEGRAM_CHAT_ID'), original['text'])
        # The durable pre-send receipt already prevents automatic resend after a crash.
        write_private(folder / 'delivered.json', {'status': 'sent', 'message_id': message_id})
        print(json.dumps({'status': 'sent', 'message_id': message_id}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'stopped', 'reason': str(error), 'automatic_retry': False}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
