# Penggunaan doforme

Mulai dari repo percobaan. Muat plugin sesuai [instalasi](INSTALLATION.md).
Daftar command/agent dan versi terkini ada di [referensi otomatis](REFERENCE.md).

## Alur utama

1. Inspeksi dan konfigurasi repo dengan init.
2. Siapkan isi issue, sumber requirement dan AC yang berlaku.
3. Periksa prasyarat lokal dengan doctor.
4. Jalankan analyze → plan → fix → test → review → pr secara manual atau melalui runner.
5. Review draft serta bukti; penerimaan bisnis dan publikasi dilakukan terpisah.

Complete berarti tahap memenuhi kontraknya, bukan issue sudah resolved. Test hijau
berlaku pada scope/AC yang diuji. Business acceptance tetap not_evaluated dan
resolution_status tetap not_established.

## Setup sekali per repo

```text
/doforme:init
/doforme:init --write
```

Command pertama tidak menulis. Command kedua membuat dua draft onboarding dan
tidak menimpa file existing. Isi `.doforme/requirements.md` dengan bukti nyata:
kutipan dokumen bisnis, tiket Jira, anotasi/desain Figma atau spec repository,
locator/version, scope yang berlaku dan konfirmasi pemilik AC. URL saja bukan
konten; persetujuan scope bukan otomatis persetujuan hasil implementasi.

Jangan menganggap salah satu sumber selalu menang atas sumber lain. Konflik
material perlu keputusan pemilik requirement. Validasi visual Figma tidak dapat
diklaim dari teks saja. Lihat [contoh sumber](requirement-input.example.md).

Profil `.doforme/repository.json` berisi requirement paths, default test commands,
temporary artifacts dan batas timeout/turn/biaya. Isikan command langsung setelah
membaca test/code/config yang dipanggil. Tidak ada izin fix/test di dalam profil.
Review dan commit setup tersebut sebelum memulai workflow yang memerlukan baseline bersih.

## Siapkan input per issue

Ekspor teks sumber dapat dibundel dengan hash/provenance menggunakan
[source snapshots](SOURCES.md). Tool ini membaca ekspor lokal yang disebut
eksplisit dan tidak memberi authority atau mengambil dokumen remote secara live.

Simpan input di luar checkout target, misalnya `/absolute/inputs/bug-123.json`:

```json
{
  "issue_ref": "BUG-123",
  "issue_text": "Halaman terakhir melewatkan item. Expected [5], observed [] untuk input yang dijelaskan di sumber requirement.",
  "edit_paths": ["pagination.py", "test_pagination.py"],
  "test_commands": ["PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination"],
  "artifact_paths": []
}
```

Ini contoh fixture pagination, bukan scope universal. Gunakan path dan runner
yang sesuai repo Anda. Issue boleh menambah sumber requirement, memilih command
khusus dan menurunkan cap. Sumber dari profil tidak dapat dihilangkan dan cap
tidak dapat dinaikkan oleh input issue.

```text
/doforme:doctor --input /absolute/inputs/bug-123.json --profile .doforme/repository.json --output /absolute/runs/bug-123
```

Output run harus belum ada, parent tersedia, serta di luar checkout target dan
plugin. Doctor tidak membuatnya. local_preflight passed hanya pemeriksaan teknis
lokal; isi/otoritas requirement dan AC masih belum dievaluasi. Lihat [doctor](PREFLIGHT.md).

Untuk melihat konfigurasi gabungan tanpa model/test/checkpoint:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --profile .doforme/repository.json --input /absolute/inputs/bug-123.json --inspect-config
```

## Menjalankan tiap tahap secara manual

Setiap command memakai konteks terpisah. Berikan laporan sebelumnya secara
eksplisit; jangan mengandalkan ingatan percakapan. Command menghasilkan laporan,
bukan otomatis menyimpan file dengan nama contoh di bawah. Simpan keluaran yang
ditinjau di lokasi laporan, atau teruskan sebagai inline input lengkap.

```text
/doforme:analyze ISSUE.md; sumber dan konfirmasi scope di REQUIREMENTS.md
/doforme:plan /absolute/reports/ANALYSIS.md
/doforme:fix /absolute/reports/PLAN.md; authorize edits ONLY pagination.py and test_pagination.py; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
/doforme:test /absolute/reports/PLAN.md /absolute/reports/FIX.md; authorize ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
/doforme:review /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md
/doforme:pr /absolute/reports/PLAN.md /absolute/reports/FIX.md /absolute/reports/TEST.md /absolute/reports/REVIEW.md
```

Analyze/plan hanya membaca. Fix butuh baseline bersih, revision plan yang sama,
scope edit tepat dan izin langsung. Fix mengamati regression failure terkait bug,
kemudian hasil sesudah perbaikan; error import/dependency bukan bukti regression.
Test terpisah mengecek AC dan hasil tool nyata. Review memeriksa content hashes,
diff dan evidence tanpa menjalankan test. PR hanya menyiapkan title/body draft;
tidak membuat PR remote atau menutup issue.

## Runner end-to-end

Lihat scope gabungan terlebih dahulu. Contoh berikut memberi izin langsung untuk
edit/test tepat sesuai input; jalankan hanya setelah Anda menyetujui scope itu:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --repo /absolute/target --profile .doforme/repository.json --input /absolute/inputs/bug-123.json --output /absolute/runs/bug-123 --allow-fix --allow-execution
```

Tanpa flag izin, runner dapat analyze/plan lalu berhenti sebelum fix. Profil atau
isi issue tidak dapat mengaktifkan flag sendiri. Padanan percakapan:

```text
/doforme:endtoend --input /absolute/inputs/bug-123.json --profile .doforme/repository.json --output /absolute/runs/bug-123; authorize output creation; authorize edits ONLY pagination.py and test_pagination.py; authorize execution ONLY PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_pagination; artifacts none
```

Runner memakai model call terpisah per tahap; batas default per tahap adalah 180
detik, 45 turns dan $1, yang dapat dibatasi lewat profil/input. Enam tahap bukan
satu panggilan; run dapat berhenti lebih awal dan memakai biaya model.

Output privat menyimpan input efektif, checkpoint, history laporan dan bukti
validasi. Jangan memasukkan credentials atau data pribadi yang tidak diperlukan.
Target saat ini dibatasi 20.000 file/100 MB dan menolak symlink/special file.
Normal permission dan audit setelah call bukan sandbox OS.

## Status, resume dan hasil blocked

Eksekusi model memakai timeout, batas output gabungan 16 MB per tahap, dan
pembersihan process group pada POSIX. Ini bukan isolasi OS atau jaminan bahwa
test tidak dapat mengakses credential yang masih diperlukan model. Lihat
[operasional dan batas isolasi](OPERATIONS.md) sebelum memakai source tidak tepercaya.

```text
/doforme:status /absolute/runs/bug-123
```

Atau baca status tanpa model:

```bash
python3 /absolute/doforme/scripts/run_workflow.py --status --repo /absolute/target --output /absolute/runs/bug-123
```

Resume memakai command runner awal dengan input, output dan izin yang sama,
ditambah --resume. Tahap interrupted/failed/blocked memerlukan --retry langsung
dan maksimal dua attempt. Retry tidak dapat melewati requirement atau verdict gate.
Changed HEAD/content/policy/config/grants menolak resume. Partial edit memerlukan
review/recovery manual; jangan reset, menghapus lock aktif, memalsukan revision
atau memperluas izin untuk memaksa kelanjutan.

Issue bukan bug atau review changes_requested dapat menghentikan handoff meskipun
tahap sebelumnya complete. Baca reason dan laporan, bukan hanya status proses.
Complete seluruh runner tetap berarti draft siap ditinjau, bukan siap publikasi.

Bukti keputusan manusia per AC dapat diperiksa dengan validator read-only di
[panduan acceptance](ACCEPTANCE.md). Bukti terikat pada konten/checkpoint/AC yang
diuji; keputusan supplied diberi label attested, bukan identitas owner yang sudah
diautentikasi. Validator ini tidak mengubah status runner atau menutup issue.

[Publikasi draft PR](PUBLISHING.md) adalah helper terpisah: default hanya preview
read-only, sedangkan POST memerlukan --publish, digest proposal yang ditinjau dan
receipt privat baru. Helper tidak melakukan push, membuat branch, merge atau
menutup issue. Commit byte-identik dapat diperiksa melalui handoff terpisah;
freshness normal status/resume dan attestation lama tidak diubah diam-diam.

## Integrasi dan pengujian

Telegram tidak wajib dikonfigurasi. Seluruh jalur manual/end-to-end serta
status/resume tetap tersedia tanpa workflow atau credential Telegram; hanya
pengiriman notifikasi yang memerlukan opt-in dan konfigurasi tambahan.

Untuk notifikasi issue bug baru dan resolved pada repo aplikasi, pakai
[konfigurasi Telegram](TELEGRAM.md). Alur manual dan end-to-end memakai gerbang
yang sama: PR merged, check wajib lulus, bukti/keputusan approver dan issue
closed/completed. Test hijau atau draft PR saja tidak mengirim status resolved.

[Pemeriksaan kesiapan integrasi](INTEGRATION-READINESS.md) menyediakan diagnosis
offline atau pembacaan metadata GitHub eksplisit. Keberadaan konfigurasi/secret
tidak dianggap bukti pengiriman berhasil. Helper tidak memasang secret, mengaktifkan
workflow, dispatch, memanggil model atau mengirim pesan.

GitHub issue intake/Telegram tetap contoh opt-in terpisah, belum aktif otomatis.
Workflow documentation hanya memeriksa docs/history dan tes offline; tidak
memproses issue atau memanggil model. Lihat [integrasi](INTEGRATIONS.md),
[uji runtime nyata](RUNTIME-0.14.md) dan [riwayat pengujian](PHASES.md).

Uji integrasi profil repo sampai draft, requirement-blocked, resume dan status
tersedia pada [workflow acceptance](RUNTIME-0.16.md). Tanpa --live hanya menampilkan
rencana; mode --live memakai repo sintetis dan dapat memanggil model sampai
delapan kali. Ini bukan cara menguji source produksi secara otomatis.

Routing `/doforme:endtoend` langsung, termasuk requirement-blocked dan kasus tanpa
izin eksekusi, diuji terpisah dalam [slash acceptance](RUNTIME-0.17.md).

Untuk mencoba issue bisnis nyata, ikuti [prosedur pilot](PILOT.md). Target repo,
izin source, requirement/AC owner dan evidence UAT harus dipilih secara eksplisit;
hasil fixture tidak dapat menggantikan pilot tersebut.

[Status roadmap](ROADMAP.md) membedakan implementasi helper, uji fixture/model,
pilot bisnis, aktivasi live dan release stabil. Nomor versi bukan bukti bahwa
seluruh kondisi operasional atau keputusan owner sudah selesai.
