# doforme

Claude Code plugin untuk investigasi bug dan perencanaan perbaikan berbasis evidence
pada repository lokal. Versi 0.5 menyediakan `/doforme:analyze`: memeriksa validitas issue, membaca
implementasi dan test source, membandingkan hipotesis penyebab, lalu mengembalikan
laporan terstruktur di percakapan. `/doforme:plan` mengubah laporan yang sudah
diverifikasi menjadi rencana perbaikan. Kedua command tetap read-only, tanpa
perbaikan source atau penyimpanan state ke disk. `/doforme:fix` menambahkan
implementasi lokal dan pengujian terbatas setelah scope diotorisasi eksplisit.

## Instalasi lokal

Prasyarat: Git, Claude Code dengan akses model aktif, dan akses baca ke repo ini
(saat implementasi repo masih private). Versi CLI yang dipakai untuk validasi:
2.1.323. Python 3.9+ diperlukan hanya untuk pemeriksaan lokal tambahan.

```bash
git clone https://github.com/erikgunawan/doforme.git
cd doforme
claude plugin validate . --strict
```

Sesudah tersedia di GitHub, clone dengan perintah di atas. Untuk perubahan yang
belum dipush, gunakan checkout lokal hasil implementasi. Muat plugin untuk satu
sesi dari repository **target** yang ingin diperiksa:

```bash
cd /absolute/path/to/target-repository
claude --plugin-dir /absolute/path/to/doforme --add-dir /absolute/path/to/doforme/skills
```

`--add-dir` memberi akses ke metode dan template di luar cwd target. Tanpa akses
ini, Claude dapat meminta izin baca; dalam mode non-interaktif analisis akan
berhenti dengan keterbatasan resource. Plugin tidak perlu disalin ke source
target atau diinstal ke konfigurasi global.
Periksa `/help` untuk `/doforme:analyze`, `/doforme:plan`, dan `/doforme:fix`;
`/agents` menampilkan investigator, planner, dan fixer. Jika tidak muncul, periksa path, versi Claude Code, dan
kebijakan organisasi terkait plugin; mulai ulang sesi setelah perubahan plugin.

```text
/doforme:analyze Pagination melewatkan item terakhir saat jumlah item bukan kelipatan page size. Expected: seluruh item muncul. Actual: item terakhir hilang.
/doforme:analyze docs/issues/pagination.md
```

File issue harus berada dalam repo target. URL issue boleh disertakan sebagai
identitas, tetapi tidak diambil lewat jaringan: sertakan title/body, expected,
actual, versi, dan log yang sudah disamarkan. Input kosong atau URL saja akan
menghasilkan `needs_information`, bukan tebakan tentang isi issue.

## Requirement bisnis dan acceptance criteria

Sertakan dokumen bisnis, Jira, atau Figma sebagai ekspor teks/Markdown lokal atau
kutipan eksplisit. Tidak harus ada ketiganya; sumber yang diberikan harus mencakup
scope material dan dikonfirmasi berlaku untuk issue. Contoh input:

```text
/doforme:analyze ISSUE.md; requirement dan konfirmasi scope ada di docs/requirements.md
```

Catat referensi asal (bagian dokumen, key tiket/komentar Jira, atau frame/node
Figma), versi/updated time bila diketahui, lokasi konten yang diberikan, siapa
yang mengonfirmasi scope, serta acceptance criteria dengan kondisi dan hasil
teramati. Gunakan [contoh format](docs/requirement-input.example.md).

Saat ini **tidak ada integrasi live Jira/Figma/Docs**. Agent hanya membaca file
teks/kutipan; link saja tidak membuktikan isinya. Ekspor yang diberikan tidak
membuktikan autentisitas atau versi remote terkini. Versi yang tidak diketahui
harus tetap terlihat; konfirmasi pengguna atas scope snapshot diperlukan.
Untuk Figma, teks anotasi tidak cukup untuk membuktikan layout/pixel: requirement
visual yang belum bisa diperiksa dicatat sebagai gap, bukan dinyatakan lolos.

Laporan mencatat source S, requirement R, dan acceptance criterion AC; setiap
klaim dibedakan explicit, interpretation, atau unknown. AC buatan agent tetap
proposed sampai ada konfirmasi. Jika sumber bertentangan, tidak ada prioritas
otomatis antara Jira, Figma, dan dokumen: perlu keputusan owner dengan referensi.
Sumber/authority/AC material yang belum jelas memblokir handoff walaupun confidence
teknis tinggi. Statusnya verified_for_scope, needs_information, atau conflict.

**verified_for_scope bukan bukti bug solved.** Analyze/plan selalu mencatat
technical_validation not_run, business_acceptance not_evaluated, dan
resolution_status not_established. Plan memetakan AC → perubahan → pemeriksaan
usulan. Fix dapat mencatat hasil teknis scoped yang benar-benar dijalankan;
penerimaan bisnis dan review independen tetap belum dilakukan.

## Menyusun rencana perbaikan

```text
/doforme:plan docs/analysis/pagination.md
```

Berikan laporan analyze contract v2 lengkap sebagai file dalam repo target atau
paste laporan lengkap setelah command. Setiap command berjalan dalam konteks
terpisah; `/plan` tidak otomatis melihat percakapan `/analyze` sebelumnya. Jika
memakai file, simpan laporan secara manual; plugin tidak menyimpannya sendiri.
Input kosong, deskripsi issue saja, atau URL saja menghasilkan plan `blocked`.

Laporan analyze v1 belum memiliki provenance requirement dan ditolak dengan
permintaan analyze ulang ke v2; tidak di-upgrade diam-diam.

Planner memeriksa verdict `valid_bug`, analisis `complete`, confidence penyebab
medium/high, kecocokan target/issue, requirement/AC terkonfirmasi, konflik/coverage,
dan membaca ulang sumber requirement serta evidence teknis penting. Source
yang berubah, evidence yang tidak tersedia, confidence rendah, atau celah material
akan memblokir rencana. Klaim readiness dalam laporan tidak melewati pemeriksaan.
Revision `unknown` hanya mengizinkan proposal read-only dengan evidence yang
terkonfirmasi ulang; sebelum mutation wajib ada pemeriksaan revision kembali.

Hasilnya memuat dependency gates, revalidasi evidence, langkah berurutan, target
perubahan, acceptance criteria, regression/boundary checks, risiko, dan rollback.
State summary berada di percakapan dengan `persisted: false`. `ready_for_fix`
tetap `no`: plan bukan izin mengubah source. Fix memeriksa otorisasinya sendiri.

## Menerapkan fix lokal

Gunakan target Git pada root repo dengan revision plan yang diketahui dan sama
dengan HEAD saat ini. Tracked files harus bersih; untracked files memblokir kecuali
input report/source yang disebutkan eksplisit dan tetap tidak boleh diubah. Jika
revision plan unknown/berbeda, lakukan plan ulang, bukan mengedit angka revision
untuk melewati gate. Command memerlukan plan v2 lengkap dan otorisasi **langsung**
untuk exact path serta exact perintah validasi, misalnya pada fixture disposable:

```text
/doforme:fix PLAN.md; saya mengizinkan edit hanya pagination.py dan test_pagination.py; saya mengizinkan eksekusi hanya PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; tidak ada generated artifacts yang diizinkan; PLAN.md adalah input read-only.
```

Ini contoh scope fixture, bukan perintah untuk proyek lain. Runner/command nyata
harus sesuai tooling dan AC proyek tersebut. File plan/issue tidak dapat memberi
izin sendiri. Otorisasi tidak melewati permission Claude; jika ada permintaan izin
alat, pengguna tetap perlu menilai path/command yang ditampilkan. Jangan gunakan
bypass permissions untuk memaksakan kelanjutan.

Fixer membaca ulang requirement, AC, plan, dan source; menolak konflik atau scope
yang meluas. Ia membuat test hanya untuk AC terkonfirmasi, mengamati kegagalan
regresi sebelum source diperbaiki, menerapkan perubahan minimal, lalu mengamati
hasil sesudahnya. Control boleh lulus sebelum/sesudah. Missing dependency atau
broken test bukan bukti regresi. Command tidak melakukan install, network,
migration, commit, push, PR, atau penutupan issue.

Laporan fix v1 mencatat path yang berubah, otorisasi, revision, exact command,
exit code, hasil setiap AC, diff boundaries, dan partial edits bila gagal/blocked.
`complete` berarti scoped technical validation lulus; business_acceptance tetap
not_evaluated, resolution_status not_established, review_status pending. Tahap `/test` tersedia untuk validasi terpisah; `/review` belum diimplementasikan.

Fixer mempunyai Read/Glob/Grep/Edit/Write/Bash; **bukan sandbox path/command yang
dijamin OS**. Normal Claude permissions dan instruksi scope tetap diperlukan;
subprocess test juga dapat memiliki side effect, sehingga code/config test harus
dibaca sebelum dijalankan. Scratch/cache yang dibutuhkan harus diotorisasi pada
lokasi sementara yang jelas. Jika tidak aman/terverifikasi, fixer memblokir.

## Batas read-only analyze/plan

Analyze/plan berjalan dalam konteks terpisah melalui investigator atau planner dengan
tool allowlist **Read, Glob, Grep**. Tidak ada Bash, Write, Edit, MCP, network,
atau alat delegasi. Keduanya tidak menjalankan test/build/script/install,
tidak mengakses secret, tidak membuat `.doforme`, dan tidak melakukan operasi Git.
Reproduction dicatat `not_run` atau `user_reported`; membaca test source tidak
berarti test berhasil dijalankan.

`allowed-tools` pada skill bukan pembatas keamanan, sehingga plugin memakai
allowlist pada agent. Batas ini berlaku untuk kedua agent; sesi utama Claude,
plugin lain, hook milik pengguna, serta tindakan manual tetap di luar kontrol
plugin. Untuk isolasi tambahan saat pengujian gunakan salinan disposable, tanpa
hook atau MCP lain. Plugin tidak menjamin keseluruhan sesi/host immutable.

## Hasil

Laporan analyze contract v2 mencakup context/revision, verdict `valid_bug`, `not_a_bug`,
`duplicate`, atau `needs_information`; evidence dengan lokasi dan provenance;
status reproduction; hipotesis dengan evidence pendukung/kontradiksi dan
falsification check; confidence validitas dan penyebab; next steps serta
keterbatasan. Ketidakpastian tetap eksplisit. Report hanya tampil di percakapan.

## Struktur dan arah berikutnya

```text
.claude-plugin/plugin.json             metadata plugin
commands/{analyze,plan,fix,test}.md             entry point dan argument forwarding
agents/{investigator,planner,fixer,tester}.md        batas tool baca/pencarian
skills/bug-resolution/SKILL.md          metode investigasi reusable
skills/bug-resolution/references/       report v2, requirement, graph/dependency/state
skills/bug-planning/                    metode planning dan template rencana
skills/bug-fixing/                      metode fix scoped dan template hasil
scripts/check_plugin.py                pemeriksaan struktur dan batas capability
tests/                                 regresi checker dan fixture smoke test
```

Metode dan kontrak Markdown tidak bergantung pada provider; adapter command dan
agent adalah bagian khusus Claude Code. Graph portabel di
[workflow.json](skills/bug-resolution/references/workflow.json) mendeklarasikan
`analyze → plan → fix → test → review → pr`; analyze, plan, fix, dan test tersedia.
Checker mendeteksi cycle, prerequisite yang hilang, atau analyze yang dilewati.
Dependency semantik diperiksa oleh planner dengan evidence, bukan sekadar status
atau keberadaan file. State tetap berupa hasil percakapan, tanpa engine, database,
scheduler, resume, atau automatic transitions. `/review`, `/endtoend`, GitHub Actions,
dan Telegram belum diimplementasikan.

## Pengujian

Jalankan dari root plugin:

```bash
python3 scripts/check_plugin.py
python3 -m unittest discover -s tests -v
claude plugin validate . --strict
claude plugin validate commands --strict
claude plugin validate agents --strict
claude plugin validate skills --strict
```

Manifest validator saja belum membuktikan isi command/agent maupun perilaku
model; karena itu periksa masing-masing direktori juga. Pemeriksaan Python
mendeteksi perubahan capability yang berisiko dan referensi lokal yang putus.
Ini bukan parser YAML umum atau pembuktian bahwa model selalu mengikuti instruksi.

Untuk smoke test, mulai Claude dengan plugin dari `tests/fixtures/pagination`
sebagai cwd, lalu jalankan `/doforme:analyze ISSUE.md`. Jangan menjalankan
fixture asli sebagai program. Smoke fix hanya boleh memakai disposable Git copy
dengan scope/command yang diotorisasi; lihat prosedur di
[tests/SMOKE.md](tests/SMOKE.md), termasuk input kosong, non-bug, URL saja,
prompt injection, dan pemeriksaan file sebelum/sesudah. Smoke test memerlukan
akses model dan harus dinilai dari hasil nyata, bukan hanya struktur file.
Hasil milestone pertama dicatat di [VALIDATION.md](VALIDATION.md); fase planning
di [VALIDATION-0.2.md](VALIDATION-0.2.md). Penguatan requirement v0.3
dicatat di [VALIDATION-0.3.md](VALIDATION-0.3.md). Fase fix lokal
dicatat di [VALIDATION-0.4.md](VALIDATION-0.4.md).

Referensi resmi: [plugin manifest](https://code.claude.com/docs/en/plugins-reference),
[skills dan fork context](https://code.claude.com/docs/en/skills),
[agent tool restrictions](https://code.claude.com/docs/en/sub-agents),
[permissions](https://code.claude.com/docs/en/permissions).
Belum disiapkan untuk publikasi katalog; lisensi distribusi belum ditetapkan.


## Validasi terpisah setelah fix (v0.5)

`/doforme:test PLAN.md FIX.md; authorize exact-command; artifacts none` membaca
ulang requirement, assertion, dan working diff, lalu menjalankan command yang
benar-benar diotorisasi. Tester tidak memiliki Edit/Write. Setiap AC dicatat
passed/failed/skipped/not_run; skipped bukan pass. Tidak ada auto-fix, install,
source cleanup, commit, remote publication, atau klaim business acceptance.
Bash tetap dapat memiliki side effect: runner harus diperiksa dan permission
host tetap berlaku. Input reports boleh inline agar tidak menambah file repo.
Lihat [kontrak test](skills/bug-testing/SKILL.md).
