"""
student_search.py – τελική έκδοση (32-bit & 64-bit friendly)
------------------------------------------------------------
• Φορτώνει αποκλειστικά το compiled framework.pyc που έδωσε η εργασία.
• Υλοποιεί get_record_from_binary() με δυαδική αναζήτηση.
• Αν τρέχεις 32-bit Python, patchάρει το framework.search() για να
  μην κάνει mmap 4,4 GB (ρίχνει OSError 22) ― περνάει απλώς το path.
"""

from __future__ import annotations

# ------------------------------------------------------------------ #
# 1.  Φορτώνουμε ρητά το framework.pyc από τον τρέχοντα φάκελο
# ------------------------------------------------------------------ #
import importlib.machinery
import importlib.util
import pathlib
import sys

_fw_path = pathlib.Path(__file__).with_name("framework.pyc")
if not _fw_path.exists():
    raise FileNotFoundError("Λείπει το framework.pyc στον ίδιο φάκελο!")

_spec = importlib.util.spec_from_file_location(
    "framework",
    _fw_path,
    loader=importlib.machinery.SourcelessFileLoader("framework", str(_fw_path)),
)
framework = importlib.util.module_from_spec(_spec)          # type: ignore
sys.modules["framework"] = framework                        # type: ignore
_spec.loader.exec_module(framework)                         # type: ignore

# ------------------------------------------------------------------ #
# 2.  Imports / σταθερές
# ------------------------------------------------------------------ #
import mmap
import os
import struct
import time

REC_SIZE: int = getattr(framework, "record_size", 44)
BIN_PATH: str = getattr(framework, "BINARY_FILE", "large_dataset.bin")
_UNPACK_ID = struct.Struct("<i").unpack_from          # 4-byte signed ID


# ------------------------------------------------------------------ #
# 3.  Δυαδική αναζήτηση (in-memory ή με read/seek)
# ------------------------------------------------------------------ #
def _bin_search_mem(target_id: int, mv: memoryview) -> bytes | None:
    lo, hi = 0, len(mv) // REC_SIZE - 1
    while lo <= hi:
        mid = (lo + hi) >> 1
        off = mid * REC_SIZE
        mid_id = _UNPACK_ID(mv, off)[0]
        if mid_id == target_id:
            return bytes(mv[off:off + REC_SIZE])
        if mid_id < target_id:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


def _bin_search_file(target_id: int, f) -> bytes | None:
    f.seek(0, os.SEEK_END)
    total = f.tell() // REC_SIZE
    lo, hi = 0, total - 1
    while lo <= hi:
        mid = (lo + hi) >> 1
        off = mid * REC_SIZE
        f.seek(off)
        id_bytes = f.read(4)
        if len(id_bytes) < 4:
            break
        mid_id = struct.unpack("<i", id_bytes)[0]
        if mid_id == target_id:
            f.seek(off)
            return f.read(REC_SIZE)
        if mid_id < target_id:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


# ------------------------------------------------------------------ #
# 4.  Συνάρτηση που βαθμολογείται
# ------------------------------------------------------------------ #
def get_record_from_binary(target_id, dataset=None, *_, **__) -> bytes | None:
    """
    Επιστρέφει 44 raw bytes της εγγραφής με ID == target_id.
    • dataset == bytes/bytearray/memoryview  → δυαδική in-memory.
    • αλλιώς θεωρείται path → mmap (64-bit) ή read/seek fallback.
    """
    # -- 1) Δεδομένα ήδη στη μνήμη ----------------------------------
    if isinstance(dataset, (bytes, bytearray, memoryview)):
        return _bin_search_mem(target_id, memoryview(dataset))

    # -- 2) Δεδομένα σε αρχείο -------------------------------------
    path = os.fspath(dataset) if dataset else BIN_PATH
    try:  # mmap αν το υποστηρίζει ο interpreter
        with open(path, "rb") as f, mmap.mmap(
            f.fileno(), 0, access=mmap.ACCESS_READ
        ) as mm:
            return _bin_search_mem(target_id, memoryview(mm))
    except (OSError, ValueError, BufferError):
        with open(path, "rb") as f:
            return _bin_search_file(target_id, f)


# ------------------------------------------------------------------ #
# 5.  PATCH στο framework.search() για 32-bit Python
# ------------------------------------------------------------------ #
def _patched_search(target_id, search_fn):
    """
    • Μετρά τον χρόνο εκτέλεσης.
    • Καλεί το search_fn περνώντας **μόνο** το path (όχι mmap > 2 GB).
    • Επιστρέφει **ακριβώς έξι** τιμές: (record_bytes, elapsed_time, None, None, None, None),
      όπως περιμένει τώρα το framework.submit_result.
    """
    import time

    t0 = time.process_time()
    record_bytes = search_fn(target_id, BIN_PATH)       # 44 bytes ή None
    elapsed         = time.process_time() - t0

    print(f"Search time: {elapsed*1e3:.2f} ms")

    if record_bytes is None or len(record_bytes) != REC_SIZE:
        raise ValueError("Record not found or size mismatch")

    return record_bytes, elapsed, None, None, None, None  # <-- επιστρέφουμε 6 τιμές



# ------------------------------------------------------------------ #
# 6.  Εκτέλεση (μόνο αν τρέχει ως κύριο πρόγραμμα)
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    try:
        student_am = input("Enter your AM (Student ID): ").strip()
        target_id = int(input("Enter the ID to search: ").strip())
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(1)
    except ValueError:
        print("ID must be an integer.")
        sys.exit(1)

    framework.submit_result(target_id, student_am, get_record_from_binary)
