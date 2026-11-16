# Bounded local execution and remaining isolation work

`scripts/execution_runtime.py` provides a reusable standard-library POSIX process
runner. Its lifecycle controls complement exact command permissions and the
existing post-call filesystem/tool audit. They do not replace an operating-system
security boundary or establish production readiness for arbitrary repository code.

## Execution contract

`run_process(argv, cwd=..., env=..., timeout_seconds=...)` uses shell=False,
closed inherited file descriptors, noninteractive stdin and a new process session.
It captures stdout and stderr with one combined byte budget (default 16 MB).
The timeout covers waiting for both the leader and inherited output pipes.

Normal completion returns ExecutionResult with returncode, bounded stdout/stderr,
captured_bytes and whether lingering descendants were terminated. A nonzero
program exit is returned as observed data, not reclassified as an infrastructure
timeout. The workflow adapter must still reject unsuccessful model results and
validate actual test evidence; a returned process result is not a stage pass.

Timeout, explicit cancellation, Ctrl-C and output overflow fail closed, terminate
the process group, escalate from TERM to KILL after a bounded grace period and
reap the leader. The same cleanup also stops same-session background descendants
that close their pipes and outlive an otherwise successful leader. There are no
automatic retries. Diagnostics use fixed messages and do not echo argv, environment
values or child stderr. Bounded partial output is available explicitly on
ExecutionError.partial_result and must be treated as private source/session data.

The default .25-second termination grace is configurable up to five seconds.
Capture limits must be explicit bounded integers, not disabled with unlimited
values. The implementation currently supports POSIX pipe/process-group behavior;
Windows process/job-object support is not claimed.

## Model environment hygiene

`model_environment()` removes nested Claude markers, inherited Git overrides,
unrelated GitHub/Telegram/cloud/SSH/container credentials and generic secret/token/
password variables while retaining the reviewed Anthropic API/OAuth credentials.
It does not modify the parent environment. Git helpers/optional-lock policy remains
the existing shared Git policy.

An operator-reviewed third-party provider may require exact additional variable
names via preserve_names. The default does not silently preserve every AWS/GCP/
Azure credential. Such deployments need separate authentication/provider testing;
the local Anthropic/OAuth validation does not establish compatibility for them.
Never derive the preservation list from an issue or repository file.

This filter is defense in depth, not complete secret isolation. Claude still
needs model authentication, and authorized child test processes may inherit that
authentication environment. Existing filesystem access, source code, credential
files, credential helpers and network reachability are not isolated by a dictionary
filter. Do not run untrusted source with valuable credentials merely because
unrelated variables were removed.

## Operational verification

Twelve offline tests ran actual subprocesses and verified bounded stdout/stderr,
nonzero exit handling, deadline/cancellation/interrupt cleanup, TERM-ignoring
descendants, background descendants with closed pipes, descendants retaining
inherited pipes, sensitive-output-safe diagnostics and environment filtering.
Zombie descendants awaiting init reaping are distinguished from running children;
the runner can reap only its own immediate child on portable POSIX.

Read-only inventory on the development host found docker and bwrap executables;
podman was absent. This inventory proves neither daemon access nor functional
user namespaces, filesystem mounts, network isolation, resource enforcement or
compatibility with the authenticated Claude CLI. No isolation backend is enabled
or silently installed by this module.

## Work still required before claiming OS isolation

The parent's read-only probes on 2026-11-16 did not establish a usable backend in
the current allowed environment: Docker could not create its runtime directory
on the read-only filesystem, and bwrap could not create user namespaces. No
daemon/settings were changed, image pulled or backend installed. These results
are environment-specific, not a statement about every deployment host.

The production ClaudeExecutor now uses this bounded process runner and sanitized
model environment. Two adapter tests verify result propagation and bounded
partial-trace retention without embedding sensitive child output in diagnostics.
The first live integration probe stopped before spawning Claude because an empty
--setting-sources value was rejected. Literal empty option values are now accepted
with a real subprocess regression; an empty executable and NUL arguments remain
invalid. A fresh probe is required rather than relabeling that failed attempt.
The fresh exported-tree probe then ran the real Claude executor successfully:
unconfirmed requirements produced blocked analyze, fresh true, unchanged HEAD
and no target edits/denials. It validates the local Anthropic/OAuth execution
path only, not every provider or all six stages under this new executor.

- A reviewed container/namespace backend with explicit mounted source/output paths,
  network policy and a suitable credential broker/separation strategy.
- Verified CPU/memory/process limits, storage limits and escape-resistant process
  cleanup. Descendants that create another session can escape a plain process group.
- Real tests of the chosen backend and model provider on the deployment host,
  including unavailable-backend and partial-edit recovery cases.
- Scale tests beyond the current runner's bounded 20,000-file/100-MB checkout and
  review of the actual commands/dependencies used by each target repository.

These are outstanding conditions, not guarantees supplied by the local runner.
The current mode remains explicitly scoped, audited local execution. No new
business acceptance, issue resolution, remote publication or integration activation
is implied by successful process lifecycle tests.
