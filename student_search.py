"""
Απλοποιημένος student_search.py
--------------------------------
• Δουλεύει απευθείας από το Drive ή τοπικά στο /content.
• Δεν κάνει mmap για 4GB (καθαρό read/seek μόνο).
• Επιστρέφει σωστά raw 44 bytes για το framework.
"""

import struct
import os
import framework  # (προϋποθέτει ότι υπάρχει το framework.pyc)

REC_SIZE = framework.record_size
BINARY_FILE = "large_dataset.bin"  # Βεβαιώσου ότι είναι στο ίδιο φάκελο
UNPACK_ID = struct.Struct("<i").unpack_from  # 4-byte integer ID

def get_record_from_binary(target_id, dataset=None):
    """Γρήγορη δυαδική αναζήτηση σε αρχείο."""
    path = BINARY_FILE if dataset is None else os.fspath(dataset)
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        total = f.tell() // REC_SIZE
        lo, hi = 0, total - 1

        while lo <= hi:
            mid = (lo + hi) // 2
            f.seek(mid * REC_SIZE)
            id_bytes = f.read(4)
            if not id_bytes:
                break
            mid_id = struct.unpack("<i", id_bytes)[0]
            if mid_id == target_id:
                f.seek(mid * REC_SIZE)
                return f.read(REC_SIZE)
            elif mid_id < target_id:
                lo = mid + 1
            else:
                hi = mid - 1
    return None

# Main πρόγραμμα για submit
if __name__ == "__main__":
    am = input("Enter your AM (Student ID): ").strip()
    tid = int(input("Enter the ID to search: ").strip())
    framework.submit_result(tid, am, get_record_from_binary)
