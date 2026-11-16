# Pilot pada repo dan issue nyata — fase 19

Pilot nyata memerlukan target dan requirement yang dipilih pemilik. Fixture
pagination bukan pengganti pilot ini dan tidak boleh dilaporkan sebagai issue
bisnis yang sudah selesai.

## Status saat persiapan

Pada 2026-11-16, pencarian issue terbuka pada erikgunawan/doforme melalui akun
GitHub yang memiliki akses menghasilkan daftar kosong. Pencarian metadata
dokumen bernama doforme di Drive yang terhubung juga tidak menemukan hasil.
Belum ada URL repo/issue pilot, keputusan scope/AC owner, atau izin mengubah
source repo lain yang diberikan. Karena itu pilot belum dijalankan.

Instruksi awal membatasi perubahan source ke doforme. Bila target berbeda,
pemilik harus menyebutkan target dan izin perubahan secara eksplisit sebelum
pekerjaan menulis di repo itu dimulai. Membaca kandidat tidak mengotorisasi fix.

## Input minimum dari pemilik

| Input | Yang harus jelas |
| --- | --- |
| Target | URL repo, issue nyata, branch/revision baseline, lingkungan yang boleh digunakan |
| Izin | Scope file yang boleh diubah, exact test commands, artifact sementara dan lokasi output |
| Requirement | Isi sumber, origin/locator/version, konfirmasi berlaku pada issue dan AC yang observable |
| Konflik | Keputusan owner untuk sumber yang bertentangan dan scope yang dikecualikan |
| Operasional | Akses model/dependency yang sudah tersedia, batas biaya/waktu dan keputusan isolasi |
| UAT | Identitas claimant owner, keputusan per AC dan evidence aktual atas konten yang diuji |

Jangan memasukkan credential ke issue, requirement atau manifest. URL saja belum
menyediakan isi sumber; file screenshot tidak otomatis memverifikasi visual/UX.

## Pelaksanaan setelah input lengkap

1. Pilih checkout/worktree terisolasi dengan baseline bersih. Jangan memakai
   perubahan working tree orang lain atau melakukan reset/stash otomatis.
2. Muat plugin, jalankan init inspection, lalu siapkan profil/input issue serta
   snapshot sumber yang benar-benar berlaku. Draft generated tidak memberi authority.
3. Jalankan doctor dan inspect-config. Review exact scope, command serta output.
4. Jalankan analyze/plan dan periksa traceability sumber → requirement → AC → test.
   Requirement/conflict/material evidence yang belum jelas harus menghentikan fix.
5. Dengan izin langsung, jalankan fix/test/review/draft. Rekam red/green aktual,
   diff minimal, content bindings, batas scope dan setiap kegagalan/denial.
6. Minta keputusan UAT owner atas konten/revisi yang diuji. Gunakan bukti penerimaan
   yang terikat konten bila tersedia; nama owner di JSON bukan autentikasi identitas.
7. Publikasi PR, notifikasi dan penutupan issue adalah tindakan terpisah. Jangan
   menyatakan resolved hanya karena pipeline complete atau test hijau.

## Laporan pilot

Catat target/issue/revision, sumber dan konfirmasi scope, exact izin, plugin policy
digest, setiap tahap/attempt, biaya teramati, test evidence, diff/hashes, keputusan
owner dan keterbatasan. Simpan raw traces dan data sensitif secara privat; history
repo hanya memuat ringkasan yang aman dan referensi evidence yang sesuai.

Keberhasilan pilot berarti perilaku pada issue nyata sesuai AC yang diuji dan
keputusan owner tercatat dengan batas autentikasi yang jelas. Pilot tidak
membuktikan keamanan arbitrary code, semua repo/framework atau kesiapan skala
produksi. Kegagalan harus dicatat, tidak diganti dengan hasil fixture sintetis.
