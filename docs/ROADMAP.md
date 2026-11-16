# Status roadmap doforme

Status per 2026-11-16. Nomor versi menandai checkpoint pengembangan, bukan bukti
bahwa semua kondisi live/produksi pada fase tersebut sudah terpenuhi. Riwayat
faktual fase 1–16 ada di [PHASES.md](PHASES.md) dan [CHANGELOG](../CHANGELOG.md).

| Fase | Hasil yang tersedia | Kondisi yang belum terpenuhi |
| --- | --- | --- |
| 17 — slash endtoend | Tiga uji Claude nyata lulus: requirement-blocked, no-execution-grant, enam tahap complete pada fixture | Bukan pilot issue nyata; run memakai policy yang diekspor dan dibekukan |
| 18 — acceptance | Validator keputusan manusia terikat source/AC/content/checkpoint; regresi AC tertukar diperbaiki | Belum ada UAT/attestation owner nyata; identitas/authority tidak diautentikasi; sebelum commit saja |
| 19 — pilot nyata | Checklist input, scope, pelaksanaan dan evidence disiapkan | Repo/issue/AC owner dan izin edit repo lain belum diberikan; pilot belum dijalankan |
| 20 — sumber requirement | Snapshot ekspor lokal berhash/provenance dengan authority tetap unconfirmed | URL sumber/akun/izin belum tersedia; tidak ada konektor live Docs/Jira/Figma yang diklaim |
| 21 — operasional | Executor POSIX terbatas, timeout/output cap/cleanup/filter env; satu probe Claude nyata lulus | Belum ada OS sandbox, CPU/memory/network isolation atau uji skala/provider luas yang tervalidasi |
| 22 — publikasi PR | Preview GET dan adapter draft POST eksplisit dengan digest/receipt; commit handoff byte-identik diuji | Belum ada proposal/head/base yang dipilih owner atau remote PR yang dibuat/divalidasi live |
| 23 — integrasi | Diagnosis offline dan metadata GitHub nyata: intake/analysis/Telegram belum dikonfigurasi | Event, sumber owner, secret/config/recipient/izin kirim belum tersedia; tidak diaktifkan atau dikirim |
| 24 — kandidat rilis | Packager/verifier reproducible dari commit bersih; hash dan gate release eksplisit | Lisensi/keputusan owner, pilot/live/isolation gates belum selesai; bukan stable/v1.0 |

## Keputusan owner yang masih diperlukan

- Repo dan issue pilot nyata, sumber/AC yang berlaku, lingkungan, exact scope dan
  izin perubahan bila memakai repo selain doforme.
- URL dokumen/Jira/Figma dan akses yang diizinkan; snapshot tidak otomatis
  membuktikan authority atau remote freshness.
- Keputusan aktivasi integrasi, autentikasi model pada runner, target notifikasi
  dan izin untuk pengujian kirim. Jangan mengirim credentials lewat issue/history.
- Branch/proposal PR untuk publikasi yang ditinjau, bila publikasi ingin dilakukan.
- Pilihan lisensi distribusi dan keputusan release stabil dari pemilik.
- Backend/deployment host yang sesuai untuk isolasi dan provider/scale testing.

Pekerjaan yang bergantung pada keputusan tersebut tetap pending, bukan dianggap
selesai melalui asumsi. Tidak ada notifikasi, PR, merge, tag atau release yang
dibuat hanya karena roadmap atau test fixture berstatus pass.

Panduan: [pilot](PILOT.md), [acceptance](ACCEPTANCE.md), [sumber](SOURCES.md),
[operasional](OPERATIONS.md), [publikasi](PUBLISHING.md),
[integrasi](INTEGRATION-READINESS.md), dan [kandidat rilis](RELEASE-CANDIDATE.md).
