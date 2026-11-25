"""Titik masuk reproduksi untuk entry ni24 V2.

Cara kerja script ini, singkatnya:
- Script ini tinggal di folder repo, berdampingan dengan compose6.py.
- Saat dijalankan, ia membaca compose6.py sebagai teks, lalu menukar satu
  baris yang menunjuk ke folder kerja asal di mesin pembuat (path absolut
  yang tidak ada di mesin lain) dengan baris yang menunjuk ke folder repo
  ini. Folder repo itu dihitung saat jalan dari lokasi file main.py
  sendiri, bukan ditulis mati di dalam kode.
- Isi compose6.py yang sudah ditukar itu lalu dijalankan di dalam proses
  ini, dengan argv seolah-olah compose6.py dipanggil langsung dengan
  subperintah "entry". compose6.py yang berjalan itulah yang menyusun
  entry.png di folder repo.
- Terakhir, script menghitung sha256 dari entry.png hasil dan
  membandingkannya dengan nilai yang diharapkan. Bila sama, reproduksi
  terbukti; bila beda, script berhenti dengan kode gagal dan pesan yang
  menjelaskan ketidaksesuaiannya.

Pemakaian:
    python3 main.py [--out <path>]
Opsi --out menyalin entry.png hasil ke path lain setelah dibuat.
"""

import hashlib
import os
import shutil
import sys

EXPECTED_SHA256 = "ffa566c75f5240b24f579c565ad3d4f659db8b9ee3b30b09a5dae58bdb1b5073"
ORIGINAL_BASE_LINE = (
    'BASE = "/home/hatch/workspace/makefun/news-image-20261124/V2/kerja-v2-skill-v5-3"'
)


def fail(message):
    print("main.py: GAGAL - " + message, file=sys.stderr)
    raise SystemExit(1)


def parse_out(argv):
    """Ambil nilai --out dari argv, atau None bila tidak diberikan."""
    if "--out" not in argv:
        return None
    i = argv.index("--out")
    if i + 1 >= len(argv):
        fail("opsi --out butuh nilai path")
    return argv[i + 1]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv):
    here = os.path.dirname(os.path.abspath(__file__))
    compose_path = os.path.join(here, "compose6.py")
    entry_path = os.path.join(here, "entry.png")
    out_path = parse_out(argv)

    try:
        with open(compose_path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        fail("tidak bisa membaca %s: %s" % (compose_path, exc))

    if ORIGINAL_BASE_LINE not in source:
        fail("baris BASE yang diharapkan tidak ditemukan di compose6.py; "
             "reproduksi dibatalkan agar tidak memakai path yang salah")

    patched = source.replace(ORIGINAL_BASE_LINE, "BASE = %r" % here, 1)

    namespace = {
        "__name__": "__main__",
        "__file__": compose_path,
        "__builtins__": __builtins__,
    }
    saved_argv = sys.argv
    sys.argv = ["compose6.py", "entry"]
    try:
        exec(compile(patched, compose_path, "exec"), namespace)
    except SystemExit as exc:
        if exc.code not in (None, 0):
            fail("compose6.py berhenti dengan kode %r" % (exc.code,))
    finally:
        sys.argv = saved_argv

    if not os.path.isfile(entry_path):
        fail("compose6.py selesai tapi entry.png tidak ditemukan di %s"
             % entry_path)

    final_path = entry_path
    if out_path:
        out_abs = os.path.abspath(out_path)
        if out_abs != os.path.abspath(entry_path):
            try:
                shutil.copyfile(entry_path, out_abs)
            except OSError as exc:
                fail("tidak bisa menyalin entry.png ke %s: %s" % (out_abs, exc))
            final_path = out_abs

    got = sha256_file(final_path)
    if got != EXPECTED_SHA256:
        fail("sha256 hasil %s tidak cocok dengan yang diharapkan %s"
             % (got, EXPECTED_SHA256))

    print("sha256: " + got)
    print("OK - entry.png cocok dengan nilai yang diharapkan: " + final_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
