# doforme

Claude Code plugin untuk investigasi bug, perencanaan berbasis requirement,
fix lokal, validasi terpisah, review, dan draft PR. Semua tahap dapat dijalankan
manual atau lewat runner lokal berurutan. Versi saat ini: **0.13.0**.

| Command | Hasil | Kemampuan |
| --- | --- | --- |
| `/doforme:init` | inspeksi repo dan draft profil dengan --write eksplisit | helper terbatas; tidak menjalankan source/test |
| `/doforme:doctor` | diagnosis prasyarat workflow baru dan daftar blocker | hanya inspeksi lokal; tidak menjalankan source/test/model |
| `/doforme:analyze` | validitas issue, evidence, hipotesis, confidence | baca/pencarian |
| `/doforme:plan` | dependency gates, langkah fix, AC → test | baca/pencarian |
| `/doforme:fix` | implementasi scoped dan red/green regression | edit/write + command terotorisasi |
| `/doforme:test` | hasil per AC: passed/failed/skipped/not_run | test terotorisasi; tanpa alat edit |
| `/doforme:review` | pass/changes_requested/blocked, findings | baca + inspeksi Git lokal |
| `/doforme:pr` | title/body draft beserta evidence | baca + inspeksi Git lokal; tanpa publikasi |
| `/doforme:endtoend` | menjalankan adapter workflow lokal | satu invocation adapter yang diotorisasi |
| `/doforme:status` | status checkpoint dan freshness | hanya membaca via helper |

**Complete tidak berarti issue resolved.** Green test berlaku pada AC yang diuji.
Review AI tidak menggantikan penerimaan pemilik requirement. Business acceptance
masih not_evaluated, resolution_status not_established, publication_ready false.
Tidak ada push, PR remote atau komentar/penutupan issue. Integrasi notifikasi
tersedia sebagai template opt-in yang tidak aktif, bukan aksi otomatis default.

## Instalasi dan penggunaan

Prasyarat: Git, Python 3.9+, Claude Code dengan akses model aktif. CLI yang diuji:
2.1.323. Gunakan checkout lokal ini sampai commit dipublikasikan oleh owner;
repo remote masih memerlukan akses dan persetujuan push terpisah.

```bash
cd /absolute/path/to/target-repository
claude --plugin-dir /absolute/path/to/doforme --add-dir /absolute/path/to/doforme/skills
```

Periksa `/help` dan `/agents`. `--add-dir` memberi akses baca metode/template di
luar cwd; tanpa akses itu command dapat berhenti. Restart/reload setelah perubahan.
Setiap command punya konteks terpisah: laporan sebelumnya harus diberikan lengkap
sebagai inline input atau file yang disebut eksplisit, bukan diasumsikan tersedia.

```text
/doforme:analyze ISSUE.md; requirement dan konfirmasi scope di REQUIREMENTS.md
/doforme:plan ANALYSIS.md
/doforme:fix PLAN.md; authorize edits ONLY pagination.py and test_pagination.py; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none; PLAN.md read-only
/doforme:test PLAN.md FIX.md; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
/doforme:review PLAN.md FIX.md TEST.md
/doforme:pr PLAN.md FIX.md TEST.md REVIEW.md
```

Contoh path/command di atas khusus fixture; scope nyata harus sesuai proyek.
Plan memerlukan analyze v2; fix memerlukan plan v2. Report fix/test/review/pr v1.
Legacy analyze v1 diblokir dan perlu re-analysis, tidak dimigrasikan diam-diam.
Plan tidak mengotorisasi source mutation: fix memeriksa scope dan revision sendiri.

## Setup per repo (v0.12)

Jalankan `/doforme:init` untuk inspeksi tanpa menulis, atau `/doforme:init --write`
untuk membuat `.doforme/repository.json` dan `.doforme/requirements.md` sebagai
draft yang belum dikonfirmasi. Tidak menimpa file yang sudah ada dan tidak
menjalankan package script/test. Review sumber bisnis/AC serta perintah test,
lalu simpan input issue dan scope edit terpisah. Lihat [panduan onboarding](docs/ONBOARDING.md).

Runner mendukung `--profile .doforme/repository.json --input /absolute/issue.json`.
Tambahkan `--inspect-config` untuk melihat hasil gabungan tanpa model call,
checkpoint, atau eksekusi. Requirement repo tetap tercakup, cap hanya bisa diturunkan
oleh issue, dan profil tidak dapat memberi izin fix/test. Config lama tetap
berfungsi tanpa --profile. Review/commit setup sebelum workflow clean-tree.

## Periksa kesiapan sebelum workflow (v0.13)

Gunakan `/doforme:doctor` dengan lokasi input issue dan profil yang dipilih
eksplisit, misalnya `/doforme:doctor --input /absolute/issue.json --profile .doforme/repository.json`.
Helper memeriksa Git root/HEAD, checkout bersih dan terbatas, konfigurasi gabungan,
sumber requirement yang dapat dibaca, scope edit, perintah test, keberadaan CLI,
serta lokasi output baru bila diberikan. Tidak memperbaiki repo, menjalankan
test/model, mengecek login, atau membuat checkpoint.

`local_preflight: passed` hanya berarti pemeriksaan lokal lulus. Isi requirement,
otoritas sumber, konflik dan cakupan AC tetap `not_evaluated`; izin fix/test serta
penerimaan bisnis tetap terpisah. Template requirement bawaan yang belum diisi
memblokir preflight. Lihat [panduan doctor](docs/PREFLIGHT.md).

## Sumber kebenaran requirement

Berikan ekspor teks/Markdown atau kutipan dokumen bisnis, Jira, Figma, repository
spec, atau konfirmasi owner. Catat origin, locator yang dibaca, versi/updated time
bila diketahui, provenance/access, serta konfirmasi berlaku untuk scope issue.
Lihat [contoh input](docs/requirement-input.example.md) dan
[kontrak evidence](skills/bug-resolution/references/requirements.md).

Tidak ada prioritas otomatis antara Jira, Figma, dan dokumen. Konflik perlu
keputusan owner dengan referensi; interpretasi dan AC usulan tetap belum
terkonfirmasi. Pemetaan S → R → AC → E/H → P → V menjaga jejak sumber hingga test.
Celah sumber/authority/AC material memblokir handoff meskipun confidence teknis tinggi.
Tidak harus ada ketiga jenis sumber jika scope tercakup sumber yang terkonfirmasi.

Belum ada integrasi live Jira/Figma/Docs atau validasi visual Figma. URL saja bukan
konten; teks anotasi bukan bukti pixel/layout. Snapshot yang diberikan tidak
membuktikan autentisitas atau versi remote terkini. Unknown tetap dicatat unknown.

## Scope fix, test, dan review

Fix memerlukan Git root, HEAD yang sama dengan revision plan, clean tracked
baseline, dan direct authorization exact edit paths/validation commands. Untracked
input report yang disebut eksplisit boleh menjadi pengecualian read-only; arbitrary
untracked source/test atau dirt lain memblokir. Jangan mengganti revision pada plan
hanya untuk melewati gate: revalidasi plan terhadap source terkini.

Fix membuat test AC terkonfirmasi, mengamati regression failure dari bug, lalu
menerapkan perubahan minimal dan memeriksa green. Control dapat pass sebelum dan
sesudah. Test terpisah membaca ulang assertions/requirement dan menjalankan hanya
command yang diotorisasi. Skipped/missing dependency tidak dihitung pass. Tidak ada
install, network, migration, test weakening, auto-reset, cleanup atau scope expansion.

Test report untuk review mengikat konten material sebelum/sesudah dengan
[Git blob snapshot](skills/bug-testing/references/snapshot.md). HEAD saja tidak
mendeteksi perubahan working tree. Reviewer membaca diff dan test baru secara
penuh, mengecek hash/freshness serta requirement; tidak menjalankan test atau fix.
PR preparation hanya menyiapkan teks, memakai referensi non-closing dan mencatat
pending human/business acceptance. Publikasi memerlukan langkah terotorisasi terpisah.

## Runner end-to-end dan checkpoint

Lihat [contoh config](docs/workflow-input.example.json). Config bukan izin sendiri;
flag pemanggil berikut mengotorisasi exact scope yang tercantum di config:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --input /absolute/config.json --output /absolute/new-output --allow-fix --allow-execution
```

Tanpa flag mutation/execution, runner dapat analyze/plan dan berhenti sebelum fix.
`/doforme:endtoend` memerlukan direct authorization output dan scope yang sama.
Target awal harus bersih, output di luar target/plugin. Saat ini runner menolak
symlink dan checkout lebih dari 20.000 file/100 MB; gunakan repo disposable kecil.
Gunakan direct local runner (contoh Python unittest); shell/install wrappers tidak
didukung. Config membatasi timeout, turns dan max_budget_usd per tahap.

Model diberi konteks baru dan explicit prior reports per tahap. Host memvalidasi
JSON envelope, tool trace, revision, actual validation tool results, dan file
boundaries. Scope/permission/format failure menghentikan proses walau model mengklaim
complete. Protokol menerima satu objek JSON lengkap, boleh dengan pengantar singkat;
field duplikat/objek ganda/hasil ambigu ditolak. Tidak ada coercion nilai verdict.

Output privat (directory mode 700, file mode 600) berisi checkpoint atomik dan
history report dengan digest. Jangan masukkan credentials atau personal data pada
input. `/doforme:status` atau helper berikut tidak menjalankan stage/menulis state:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --status --repo /absolute/target --output /absolute/output
```

Resume memakai command awal dengan input/scope flags yang sama dan `--resume`.
Blocked/failed/interrupted stage memerlukan `--retry` eksplisit; maksimal dua
attempt, tidak otomatis. Changed HEAD/config/grant/source/report/plugin policy
menolak resume. Partial edit perlu review/recovery manual. Lock membatasi satu
runner; setelah kematian proses keras, pastikan pemilik telah berhenti sebelum
pemulihan manual. Tidak ada reset/delete/Git mutation untuk memaksakan resume.

Graph v2: [workflow.json](skills/bug-resolution/references/workflow.json).
Checkpoint file schema v1 berbeda dari state summary report v1: stage agent tidak
menyimpan state (`persisted: false`); host yang dipanggil eksplisit dapat menyimpan
checkpoint (`host_persisted: true`). Digest mendeteksi inkonsistensi, bukan forgery
oleh pihak yang menguasai source dan state sekaligus.

## Batas kemampuan dan pengujian

Analyze/plan hanya Read/Glob/Grep. Tester/reviewer/PR preparer memiliki Bash terbatas
oleh metode dan permission host. Fixer memiliki Edit/Write/Bash. **Ini bukan sandbox
OS**: subprocess test bisa punya side effect dan audit trace terjadi setelah call.
Code/config runner perlu diperiksa; normal Claude permissions tetap berlaku. Runner
menolak tool/command di luar scope dan unexpected diff; tidak menjamin kebenaran
semantik requirement atau keamanan semua proses/plugin lain. Built-in plugins
Claude tetap bisa hadir. Hasil uji fixture bukan bukti kesiapan produksi umum.

```bash
python3 scripts/check_plugin.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate commands --strict
claude plugin validate agents --strict
claude plugin validate skills --strict
```

[Riwayat fase dan hasil pemeriksaan](docs/PHASES.md),
[smoke acceptance cases](tests/SMOKE.md), serta VALIDATION.md dan VALIDATION-0.2
hingga VALIDATION-0.4 mencatat pengujian awal pada fixture sintetis. Tes deterministic
adapter memakai fake executor; hasil model nyata dicatat terpisah. Lisensi distribusi,
ikon dan packaging katalog belum ditetapkan; katalog belum siap dipublikasikan.

Referensi resmi: [manifest](https://code.claude.com/docs/en/plugins-reference),
[skills](https://code.claude.com/docs/en/skills),
[agent restrictions](https://code.claude.com/docs/en/sub-agents),
[permissions](https://code.claude.com/docs/en/permissions).


## Integrasi opsional (v0.10)

[Template GitHub issue + Telegram](integrations/github-issues.yml.example) berada
di luar folder workflow aktif. Default hanya dry-run packet lokal. Analisis
read-only, instalasi CLI yang dipin operator, dan notifikasi Telegram memerlukan
opt-in/secret terpisah; auto-fix, publikasi, dan notifikasi resolved tidak diaktifkan.
Lihat [instruksi integrasi dan batasnya](docs/INTEGRATIONS.md). Tidak ada secret yang
dipasang, workflow GitHub dijalankan, atau pesan nyata dikirim pada implementasi.
Host menyimpan command, exit code dan tool output validasi dalam artifact privat
untuk audit; field hasil model bukan pengganti observed test evidence. Credential
GitHub/Telegram tidak diteruskan ke child model. Timeout/import/dependency error
bukan bukti regression failure. Parser failure/permission denial tetap berhenti.


## Kesiapan rilis lokal (v0.11)

[Catatan hardening dan verifikasi](docs/RELEASE-0.11.md) menjelaskan reproduksi
bug scope/status dan perbaikannya. Path dinormalisasi sebelum pemeriksaan overlap;
artifact baru tidak boleh menunjuk source yang sudah ada. Status dan resume
memeriksa history, report yang ditampilkan, serta evidence yang diwajibkan.
Analisis bukan-bug dan review yang meminta perubahan menghentikan handoff tanpa
mengubah hasil tahap menjadi kegagalan palsu. Retry tidak dapat melewati gate.
Inspeksi Git menggunakan prefix `git -c core.fsmonitor=false --no-optional-locks`
dan diff `--no-ext-diff --no-textconv`; inherited Git override/helper dinonaktifkan.
Snapshot menolak named pipe/socket, bukan membukanya. Versi ini lulus 73 tes lokal;
checkpoint dari policy lama perlu run baru, tidak dimigrasikan diam-diam.
