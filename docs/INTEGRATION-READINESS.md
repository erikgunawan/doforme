# Pemeriksaan kesiapan integrasi — fondasi fase 23

Helper pada halaman ini memeriksa template intake legacy. Untuk workflow
standalone bug-baru/resolved v0.25, gunakan [konfigurasi Telegram](TELEGRAM.md);
hasil pemeriksa legacy tidak dianggap validasi live atas workflow baru tersebut.

Helper ini memeriksa prasyarat GitHub issue intake dan Telegram tanpa memasang
workflow, mengubah variable/secret, menjalankan workflow/model atau mengirim
pesan. Default sepenuhnya offline. Fase aktivasi live belum selesai tanpa issue
pilot, sumber/AC terkonfirmasi, akun/secret yang berlaku dan penerima yang dipilih
pemilik. Tidak ada penerima atau approval yang disimpulkan dari konfigurasi.

```bash
python3 -B /absolute/doforme/scripts/integration_readiness.py --repo /absolute/target --repository owner/repo --event /absolute/inputs/issue-event.json --requirement requirements/confirmed-source.md
```

Nama repository remote wajib eksplisit dan berformat owner/name. Event opsional
harus snapshot issue opened yang cocok dengan repository/URL issue yang dipilih;
isi event tetap tidak tepercaya dan tidak membuktikan event live pernah diterima.
--requirement dapat diulang untuk maksimal 16 path sumber lokal yang secara
eksplisit dipilih operator. Source body tidak dijalankan dan tidak menjadi izin.

Helper juga dapat memeriksa metadata GitHub dengan akun CLI yang sudah memiliki
akses, hanya jika --check-remote diberikan langsung:

```bash
python3 -B /absolute/doforme/scripts/integration_readiness.py --repo /absolute/target --repository owner/repo --requirement requirements/confirmed-source.md --check-remote
```

Panggilan ini memakai gh api GET ke github.com untuk daftar repository workflow,
variables, nama secret, dan isi workflow intake bila aktif. Ia tidak membaca
nilai secret atau menampilkan variable lain. Metadata hanya tingkat repository;
applicability secret environment/organisasi tidak ditebak. Daftar tidak lengkap
atau akses ditolak menghasilkan blocked, bukan klaim bahwa credential tidak ada.
--telegram-recipient menerima ID/nama chat yang diberikan operator secara
eksplisit, namun helper tidak dapat membuktikan ID itu cocok dengan secret chat.

## Arti status

- not_checked: pemeriksaan belum dilakukan atau input belum diberikan.
- not_configured: prasyarat konfigurasi yang diperiksa belum tersedia.
- configured: konfigurasi/metadata terlihat; bukan bukti eksekusi atau delivery.
- blocked: input tidak valid, metadata tidak lengkap, akses gagal, atau workflow
  lokal berbeda dari template yang sedang diperiksa dan perlu review.

live_verification selalu not_checked dan ready_to_activate tetap false. Tidak ada
state verified_live yang dihasilkan dari nama secret atau workflow aktif saja.
Exit code 0 berarti laporan berhasil dibuat, bukan integrasi siap diaktifkan.
Laporan tidak menyatakan requirement verified_for_scope atau bisnis accepted.

## Prasyarat dan urutan aktivasi manual

1. Pilih repo/issue pilot dan data yang diizinkan; review isi event serta sumber
   requirement dan konfirmasi owner terhadap AC. Jangan memakai synthetic fixture
   sebagai penerimaan bisnis nyata.
2. Review [template intake](../integrations/github-issues.yml.example), lalu
   tempatkan salinan yang disetujui di .github/workflows/doforme-intake.yml pada
   repo yang memuat scripts/skills plugin. Helper readiness tidak menyalinnya.
3. Mulai dengan mode packet dry-run. Periksa satu event issue opened nyata,
   artifact privat dan deduplikasi. workflow_dispatch tanpa issue menghasilkan
   skipped; keberhasilan job manual itu bukan bukti intake issue live.
4. Jika analisis live diotorisasi, sediakan DOFORME_ENABLE_ANALYZE=true, versi
   numerik yang ditinjau di DOFORME_CLAUDE_VERSION, ANTHROPIC_API_KEY yang berlaku,
   serta DOFORME_TRUSTED_REQUIREMENTS sesuai path operator. Nama secret saja tidak
   membuktikan login/model, CLI kompatibel atau requirement benar.
5. Jika notifikasi diotorisasi, pilih penerima dan review data yang boleh dikirim;
   sediakan DOFORME_NOTIFY_TELEGRAM=true serta TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID.
   Satu test send memerlukan otorisasi terpisah dan hasil delivery aktual. Helper
   ini tidak menguji bot atau mengirim pesan untuk memeriksa token.
6. Periksa receipt sebelum recovery. Delivery tidak pasti tidak di-retry otomatis;
   receipt lokal belum memberikan deduplikasi global antar rerun GitHub.

Template default membatasi permissions contents:read dan tidak mengaktifkan
auto-fix/publikasi. Source dari variable harus sesuai input --requirement yang
ditinjau; variabel tidak dapat mengotorisasi edit atau eksekusi source. Helper
memeriksa workflow remote cocok dengan byte template yang disediakan, bukan
mengklaim audit keamanan lengkap atas YAML, account policy atau subproses.

## Verifikasi

Tes offline memakai metadata reader yang diinjeksikan dan repo sementara untuk
memastikan default tidak menghubungi GitHub, event/repo benar, metadata bounded,
workflow/opt-in/version/source path diperiksa, nama secret tidak dianggap sukses,
dan tidak ada setup/send/dispatch. Sumber FIFO/symlink ditolak sebelum dibuka.
CLI memiliki mode laporan saja; tidak ada --activate atau --send-telegram.
Uji metadata remote nyata, jika dilakukan, tetap berbeda dari verifikasi live.

Pada 2026-11-16, pemeriksaan metadata read-only pada erikgunawan/doforme berhasil
mengobservasi konfigurasi repository. Workflow intake belum terpasang/aktif,
analisis/notifikasi tidak diaktifkan, versi CLI belum disediakan, dan tiga nama
secret yang diharapkan belum terlihat pada tingkat repository. Tidak ada input
event/sumber/owner AC/penerima yang diberikan untuk pengujian live. Laporan
tersanitasi disimpan privat di artifacts workstation; ini bukan bukti tentang
secret environment/organisasi. Tidak ada credential value dibaca, setup diubah,
workflow didispatch, model dipanggil atau pesan dikirim.

Validasi skema API menolak row workflow/secret malformed sebagai blocked, bukan
mengartikannya sebagai konfigurasi tidak ada. Isi workflow remote harus berupa
file dengan path yang diminta dan base64 valid sebelum dibandingkan ke template.

Referensi resmi: [GitHub secret metadata](https://cli.github.com/manual/gh_secret_list),
[repository workflows](https://docs.github.com/en/rest/actions/workflows), dan
[pemakaian secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).
