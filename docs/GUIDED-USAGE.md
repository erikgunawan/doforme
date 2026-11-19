# doforme dengan command singkat

Anda memilih issue dan menyetujui keputusan yang relevan. Plugin menangani
pencarian tiket, setup, input internal, penyimpanan laporan, dan handoff tahap.
Mulai sesi Claude Code baru setelah memperbarui plugin.

## 1. Setup repo

```text
/doforme:init
```

Doforme membaca repo, menawarkan sumber requirement serta kandidat command test,
dan meminta konfirmasi AC yang berlaku. Ia memeriksa kode runner/test sebelum
mengusulkan command; menemukan script bukan otomatis memberi izin menjalankannya.

Contoh percakapan:

> Saya menemukan tiket BUG-301 dan aturan D3. Usulan AC: task in_progress tampil
> di kolom Dikerjakan; jumlah task tidak berubah. Apakah AC ini berlaku?

Setelah keputusan Anda dicatat, doforme menampilkan perubahan ke dua file
konfigurasi dan bertanya apakah konfigurasi tersebut boleh disimpan. File existing
ditinjau, bukan diam-diam diganti. AC yang belum disetujui tetap ditandai demikian.
Tidak ada test/source yang dijalankan oleh setup.

Review dan commit konfigurasi sebelum run. Jika worktree belum bersih, doforme
menjelaskan file yang menghalangi; ia tidak melakukan commit, reset, atau stash.
`ready_for_fix: false` pada hasil helper init bukan error: setup bukan izin fix.

## 2. Pilih issue

```text
/doforme:analyze BUG-301
```

ID lokal harus cocok dengan satu file di docs/bugs. Anda juga bisa memilih
`#3`, URL GitHub issue dari origin repo ini, atau satu file tiket di docs/bugs.
Untuk #number/URL, helper hanya membaca metadata GitHub melalui gh; ia tidak
membuat issue, komentar, atau pesan Telegram. Tanpa argumen, doforme menawarkan
pilihan atau meminta identitas issue.

Doforme menampilkan lokasi laporan dan batas pemakaian model sebelum run baru.
Default lokasi privat: ~/.local/state/doforme, dipisahkan berdasarkan checkout
dan issue. Laporan dan checkpoint disimpan otomatis di luar repo. Analisis tetap
read-only terhadap source; penyimpanan laporan dilakukan host, bukan investigator.
Tidak ada izin edit atau test hanya karena Anda menjalankan analyze.

## 3. Lanjutkan tanpa menyalin laporan

```text
/doforme:plan BUG-301
/doforme:fix BUG-301
/doforme:test BUG-301
/doforme:review BUG-301
/doforme:pr BUG-301
```

Setiap command memakai laporan tersimpan yang terikat pada run dan source.
Sebelum fix, doforme membaca plan dan menunjukkan scope konkret:

> Ubah: js/dashboard.js, tests/dashboard.test.js
>
> Jalankan untuk Fix dan Test: node tests/run-node.js
>
> Artefak: tidak ada. Publikasi: tidak ada. Lanjut dengan scope ini?

Jawaban singkat seperti “ya” berlaku untuk proposal yang baru ditampilkan di
percakapan itu. File laporan, config, issue, atau jawaban dari sesi lama tidak
menggantikan persetujuan langsung. Scope yang berubah harus ditinjau lagi.

Jika langsung memanggil fix sebelum ada analisis/plan, doforme menunjukkan
command berikutnya yang diperlukan. Ia tidak memperbaiki source atau diam-diam
menjalankan seluruh tahap pendahulu. Anda dapat menyetujui langkah berikutnya
langsung di percakapan, tanpa menyusun prompt baru.

## 4. End-to-end

```text
/doforme:endtoend BUG-301
```

Plugin mempersiapkan issue, menjalankan analyze dan plan, lalu meminta persetujuan
scope hasil plan sebelum melanjutkan fix → test → review → draft PR. Bukti yang
kurang atau requirement yang belum jelas dapat menghentikan run lebih awal.
Ini bukan satu persetujuan umum untuk semua file, test, atau publikasi.

## 5. Status, retry, dan run baru

```text
/doforme:status BUG-301
/doforme:analyze BUG-301 --new
```

Status menunjukkan hasil, lokasi laporan, freshness, dan langkah berikutnya tanpa
memanggil model. Run baru mempertahankan session lama dan tidak mewarisi izin edit
run lama. Siapkan baseline bersih; jangan reset atau menghapus perubahan parsial
untuk membuat run lolos.

Tahap blocked/failed/interrupted tidak diulang diam-diam. Baca alasan, lalu
minta retry secara eksplisit (`--retry`) bila kondisi run masih valid. Batasnya
maksimal dua percobaan per tahap. Perubahan issue, requirement, konfigurasi,
source/HEAD, atau policy plugin dapat mengharuskan run baru. Lock aktif menolak
run baru; jangan menghapus lock untuk melewati proses yang masih berjalan.

## Mode advanced dan batas validasi

Mode lama dengan file laporan lengkap, --input/--profile/--output, serta izin
langsung tetap tersedia. Mode manual advanced mengembalikan laporan dalam chat;
penyimpanan otomatis di panduan ini berlaku untuk mode terpandu berdasarkan issue.
Untuk inspeksi onboarding lama, gunakan `/doforme:init --inspect`; `--write`
tetap hanya membuat dua draft, bukan mengonfirmasi requirement.

Penyimpanan scope adalah catatan persetujuan yang diberikan pemanggil, bukan
verifikasi identitas manusia. Engine tetap memeriksa kontrak hasil, bukti tool,
revisi, dan batas file/command. Prompt dan audit bukan sandbox OS. Test hijau
bukan bukti acceptance bisnis; draft PR tidak memublikasikan perubahan. Detail:
[penggunaan advanced](USAGE.md), [operasional](OPERATIONS.md),
[acceptance](ACCEPTANCE.md), [publikasi](PUBLISHING.md), dan [Telegram](TELEGRAM.md).
