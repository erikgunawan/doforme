# doforme

Claude Code plugin untuk investigasi bug berbasis evidence pada repository lokal.
Milestone 1 menyediakan `/doforme:analyze`: memeriksa validitas issue, membaca
implementasi dan test source, membandingkan hipotesis penyebab, lalu mengembalikan
laporan terstruktur di percakapan. Tidak ada perbaikan source atau penyimpanan state.

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
Periksa `/help` untuk `/doforme:analyze` dan `/agents` untuk
`doforme:investigator`. Jika tidak muncul, periksa path, versi Claude Code, dan
kebijakan organisasi terkait plugin; mulai ulang sesi setelah perubahan plugin.

```text
/doforme:analyze Pagination melewatkan item terakhir saat jumlah item bukan kelipatan page size. Expected: seluruh item muncul. Actual: item terakhir hilang.
/doforme:analyze docs/issues/pagination.md
```

File issue harus berada dalam repo target. URL issue boleh disertakan sebagai
identitas, tetapi tidak diambil lewat jaringan: sertakan title/body, expected,
actual, versi, dan log yang sudah disamarkan. Input kosong atau URL saja akan
menghasilkan `needs_information`, bukan tebakan tentang isi issue.

## Batas read-only

Command berjalan dalam konteks terpisah melalui `doforme:investigator` dengan
tool allowlist **Read, Glob, Grep**. Tidak ada Bash, Write, Edit, MCP, network,
atau alat delegasi. Investigator tidak menjalankan test/build/script/install,
tidak mengakses secret, tidak membuat `.doforme`, dan tidak melakukan operasi Git.
Reproduction dicatat `not_run` atau `user_reported`; membaca test source tidak
berarti test berhasil dijalankan.

`allowed-tools` pada skill bukan pembatas keamanan, sehingga plugin memakai
allowlist pada agent. Batas ini berlaku untuk investigator; sesi utama Claude,
plugin lain, hook milik pengguna, serta tindakan manual tetap di luar kontrol
plugin. Untuk isolasi tambahan saat pengujian gunakan salinan disposable, tanpa
hook atau MCP lain. Plugin tidak menjamin keseluruhan sesi/host immutable.

## Hasil

Laporan contract v1 mencakup context/revision, verdict `valid_bug`, `not_a_bug`,
`duplicate`, atau `needs_information`; evidence dengan lokasi dan provenance;
status reproduction; hipotesis dengan evidence pendukung/kontradiksi dan
falsification check; confidence validitas dan penyebab; next steps serta
keterbatasan. Ketidakpastian tetap eksplisit. Report hanya tampil di percakapan.

## Struktur dan arah berikutnya

```text
.claude-plugin/plugin.json             metadata plugin
commands/analyze.md                    entry point dan argument forwarding
agents/investigator.md                 batas tool baca/pencarian
skills/bug-resolution/SKILL.md          metode investigasi reusable
skills/bug-resolution/references/       report, workflow, dependencies, state v1
scripts/check_plugin.py                pemeriksaan struktur dan batas capability
tests/                                 regresi checker dan fixture smoke test
```

Metode dan kontrak Markdown tidak bergantung pada provider; adapter command dan
agent adalah bagian khusus Claude Code. Graph/dependency/state baru berupa
kontrak kecil berversi. Belum ada engine, database, scheduler, resume, atau
implementasi `/plan`, `/fix`, `/endtoend`, GitHub Actions, maupun Telegram.
Readiness untuk planning hanya rekomendasi, tidak memicu command lain.

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
fixture sebagai program. Kriteria penerimaan terdapat di
[tests/SMOKE.md](tests/SMOKE.md), termasuk input kosong, non-bug, URL saja,
prompt injection, dan pemeriksaan file sebelum/sesudah. Smoke test memerlukan
akses model dan harus dinilai dari hasil nyata, bukan hanya struktur file.
Hasil pemeriksaan implementasi ini dicatat di [VALIDATION.md](VALIDATION.md).

Referensi resmi: [plugin manifest](https://code.claude.com/docs/en/plugins-reference),
[skills dan fork context](https://code.claude.com/docs/en/skills),
[agent tool restrictions](https://code.claude.com/docs/en/sub-agents).
Belum disiapkan untuk publikasi katalog; lisensi distribusi belum ditetapkan.
