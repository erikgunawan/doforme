# Publikasi draft PR yang terkontrol

`/doforme:pr` tetap hanya menyiapkan teks lokal. Adapter terpisah ini dapat
memeriksa proposal terhadap repo/branch GitHub yang dipilih eksplisit, lalu
membuat **draft** PR hanya dengan flag publikasi dan digest yang sudah ditinjau
pemanggil. Default-nya hanya GET/read-only; tidak membuat branch atau push.

Tidak ada PR nyata yang dibuat selama implementasi fitur ini. Unit test memakai
GitHub client mock; ketersediaan akses/branch GitHub sebenarnya dan keputusan
review owner tetap diperlukan untuk pemakaian live.

## Prasyarat dan handoff commit

- Git, Python, `gh` yang terautentikasi untuk github.com dan repo tujuan eksplisit.
- Checkpoint workflow complete dengan review pass, seluruh artifact/digest valid,
  policy plugin yang sama dan konten target identik dengan snapshot yang diuji.
- Origin target harus menunjuk repo GitHub yang sama. Input repo tidak peka
  huruf besar/kecil; setelah GET metadata diverifikasi, adapter memakai nama
  kanonis GitHub untuk binding, request berikutnya, receipt dan verifikasi URL.
  Gunakan dua branch existing yang berbeda dan tidak ada PR open
  untuk head/base tersebut.
- Seluruh tree head remote harus identik dengan blob/mode snapshot tested,
  head merupakan descendant dari baseline tested, serta diff base→head tidak
  kosong dan tidak melampaui edit_paths. Symlink, submodule, tree terpotong dan
  temporary artifact workflow belum didukung untuk publikasi.
- Title/body harus berasal dari file lokal yang ditinjau manusia. Field closing
  seperti Fixes #N, Closes owner/repo#N atau Resolves URL issue ditolak; gunakan
  referensi non-closing seperti Refs #N.

Workflow normal mengikat baseline HEAD dan perubahan working tree. Commit/push
patch yang diuji memang mengubah HEAD. Adapter menyediakan **handoff terpisah**:
jika HEAD berubah, ia mensyaratkan checkout bersih, baseline tested masih ancestor,
dan seluruh tree commit baru tepat sama dengan konten yang diuji. Proposal
mencatat revision_transition dengan tested_revision serta current_revision.

Checkpoint/report asli tidak diedit atau direbind. `/doforme:status` dan resume
normal tetap boleh menandai checkpoint stale karena HEAD berubah. Handoff hanya
menyatakan commit baru memuat byte/mode yang sama; ia tidak menganggap laporan
lama dibuat pada commit baru. Perubahan tambahan dari commit hook atau format
otomatis yang mengubah byte diuji akan menolak handoff. File ignored/untracked
yang ada pada snapshot tested juga harus dipertimbangkan sebelum publikasi:
adapter menuntut tree remote lengkap cocok, bukan hanya dua file source terlihat.

Owner mengatur commit dan push sendiri melalui prosedur repo yang berlaku, di
luar adapter ini. Jika ingin menjaga checkout baseline untuk audit, owner dapat
menyiapkan commit di worktree terpisah; adapter tetap memverifikasi tree remote
terhadap snapshot asli. Tidak ada push otomatis untuk menyelesaikan mismatch.

## Preview read-only

Siapkan title satu baris (maksimal 256 karakter) dan body dengan bukti/risiko yang
ditinjau. Body proposal otomatis menyatakan penerimaan bisnis serta penyelesaian
issue belum dievaluasi/dibuktikan; persiapan draft tidak mengesahkan bisnis.

```bash
python3 -B /absolute/doforme/scripts/publish_pr.py --repo /absolute/target --workflow /absolute/run --repository owner/project --head fix-branch --base main --title-file /absolute/title.txt --body-file /absolute/body.md
```

Periksa preview, changed_paths, head/base SHA dan revision_transition. Digest
mengikat teks yang akan dikirim, repo/branch/commit remote serta source dan
checkpoint. Preview menggunakan GitHub GET requests, jadi ini bukan pemeriksaan
offline. Tidak ada file receipt atau aksi remote write yang dibuat pada preview.
publication_ready tetap false: hasil ini belum merupakan izin publikasi,
autentikasi review manusia, acceptance bisnis atau kesiapan merge/deploy.

## Publikasi eksplisit satu kali

Hanya setelah pemanggil meninjau proposal dan memang mengotorisasi pembuatan
draft PR, sediakan receipt **baru** dalam folder privat existing (mode 700),
di luar target, folder workflow dan checkout plugin:

```bash
python3 -B /absolute/doforme/scripts/publish_pr.py --repo /absolute/target --workflow /absolute/run --repository owner/project --head fix-branch --base main --title-file /absolute/title.txt --body-file /absolute/body.md --publish --expected-digest COPY_REVIEWED_PREVIEW_DIGEST --receipt /absolute/private-receipts/new-attempt.json
```

Adapter mengulang verifikasi lokal/remote dan menolak jika digest berubah. Ia
menulis receipt eksklusif attempting serta menyinkronkannya ke disk sebelum
POST. Seluruh payload dikirim sebagai JSON stdin ke fixed-host `gh api`; isi
issue/body tidak diinterpolasi ke shell. Adapter menggunakan POST pulls langsung,
bukan `gh pr create`, agar tidak memicu alur interaktif/auto-push CLI.

| Receipt/status | Tindakan |
| --- | --- |
| draft_created | API mengonfirmasi draft pada repo dan SHA yang ditinjau; review manusia berikutnya tetap diperlukan |
| created_needs_manual_review | API membuat PR, tetapi SHA bergerak selama request; periksa PR secara manual, jangan menganggap content binding valid |
| uncertain | Request/response gagal atau tidak membuktikan draft yang diharapkan; PR mungkin sudah tercipta, periksa GitHub sebelum tindakan berikutnya |
| attempting tersisa | Proses berhenti sesudah receipt dibuat; perlakukan sebagai outcome belum diketahui |

Tidak ada retry otomatis, penghapusan receipt, penutupan PR atau rollback remote.
Receipt yang sudah ada selalu menghalangi POST ulang. Ini deduplikasi per receipt,
bukan exactly-once global bila operator memilih file baru atau menjalankan banyak
mesin. Duplicate open-PR check juga dilakukan, tetapi branch/open-PR dapat berubah
di antara GET dan POST. API pembuatan draft di sini tidak memiliki atomic pin
head/base SHA; hasil response diperiksa untuk mendeteksi race dan dilaporkan
untuk review manual, bukan disembunyikan.

Hanya draft PR dibuat. Tidak ada merge, auto-merge, branch creation, push, komentar,
notifikasi, issue closure atau acceptance bisnis otomatis. Exit 0 pada hasil
created_needs_manual_review juga bukan bukti binding masih benar: consumer harus
membaca status/content_binding. Gagal atau uncertain tidak boleh diatasi dengan
memilih receipt baru tanpa pemeriksaan manual.

## Batas pengujian dan referensi

Tes lokal memakai commit patch yang benar-benar mengubah HEAD, membuktikan
handoff byte-identik tanpa mengubah checkpoint/freshness runner normal. Input repo
dengan casing berbeda diuji sampai respons POST mocked, sehingga URL kanonis
yang sah tidak salah ditandai uncertain. Tes juga
menguji mismatch tree remote, source baru, closing references, digest stale,
receipt sebelum POST, uncertain delivery, deduplikasi dan race branch. Test
checkpoint/hasil GitHub adalah sintetis; belum ada demonstrasi live publication.

Referensi resmi: [GitHub create pull request](https://docs.github.com/en/rest/pulls/pulls#create-a-pull-request),
[branch metadata](https://docs.github.com/en/rest/branches/branches#get-a-branch),
[Git trees](https://docs.github.com/en/rest/git/trees#get-a-tree), dan
[gh pr create behavior](https://cli.github.com/manual/gh_pr_create).
