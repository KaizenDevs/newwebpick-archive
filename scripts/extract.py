#!/usr/bin/env python3
"""Extract SWFs from NewWebPick Flash projectors and app bundles."""

import os
import shutil
import struct

SOURCE = os.path.expanduser("~/Documents/NewWebPick")
DEST = os.path.join(os.path.dirname(__file__), "..", "site", "swf")

ISSUES = [
    ("01", "NewWebPick 01.app"),
    ("02", "NewWebPick 02"),
    ("03", "NewWebPick 03"),
    ("04", "NewWebPick 04"),
    ("05", "NewWebPick 05"),
    ("06", "NewWebPick 06"),
    ("07", "NewWebPick 07"),
    ("08", "NewWebPick 08"),
    ("09", "NewWebPick 09"),
    ("10", "NewWebPick 10"),
    ("11", "NewWebPick 11"),
    ("12", "NewWebPick 12"),
    ("13", "NewWebPick 13"),
    ("14", "NewWebPick 14"),
    ("15", "NewWebPick 15"),
    ("16", "Newwebpick 16"),
    ("17", "NewWebPick 17"),
    ("18", "newwebpick 18"),
    ("19", "newwebpick 19"),
    ("20", "newwebpick 20"),
    ("21", "newwebpick_21_full"),
    ("22", "newwebpick_22_full"),
    ("23", "newwebpick_23_full"),
    ("24", "newwebpick_24_full"),
    ("25", "newwebpick_25_full"),
    ("26", "newwebpick_26_full"),
    ("27", "newwebpick_27_full"),
    ("28", "newwebpick_28_full"),
    ("29", "newwebpick_29_full"),
    ("30", "newwebpick_30_full"),
    ("31", "newwebpick_31_full"),
    ("32", "newwebpick_32_full"),
    ("33", "newwebpick_33_full"),
    ("34", "newwebpick_34_full"),
    ("35", "newwebpick_35_full"),
    ("36", "newwebpick_36_full.app"),
    ("37", "newwebpick_37_full.app"),
    ("38", "newwebpick_38_full.app"),
    ("39", "newwebpick_39_full.app"),
    ("40", "newwebpick_40_full.app"),
    ("41", "newwebpick_41_full.app"),
    ("42", "newwebpick_42_full.app"),
    ("43", "newwebpick_43_full.app"),
    ("44", "newwebpick_44_full.app"),
]


def extract_from_projector(path):
    """Find the main SWF embedded in a Flash projector binary."""
    data = open(path, "rb").read()
    filesize = len(data)
    best = None
    best_delta = filesize

    for sig in (b"FWS", b"CWS"):
        idx = 0
        while True:
            idx = data.find(sig, idx)
            if idx == -1:
                break
            if idx + 8 > filesize:
                idx += 1
                continue
            length = struct.unpack_from("<I", data, idx + 4)[0]
            # Pick candidate closest to filling the file from its offset
            delta = abs((idx + length) - filesize)
            if delta < best_delta:
                best_delta = delta
                best = (idx, length)
            idx += 1

    if best is None:
        return None
    idx, length = best
    return data[idx : idx + length]


def main():
    os.makedirs(DEST, exist_ok=True)
    for num, name in ISSUES:
        src = os.path.join(SOURCE, name)
        dest = os.path.join(DEST, f"newwebpick_{num}.swf")

        if not os.path.exists(src):
            print(f"[MISSING] {name}")
            continue

        # App bundle with movie.swf inside
        bundle_swf = os.path.join(src, "Contents", "Resources", "movie.swf")
        if os.path.isdir(src) and os.path.exists(bundle_swf):
            shutil.copy2(bundle_swf, dest)
            print(f"[COPY]    {num} ← {name}/Contents/Resources/movie.swf")
            continue

        # Single-file projector — extract embedded SWF
        if os.path.isfile(src):
            swf = extract_from_projector(src)
            if swf:
                open(dest, "wb").write(swf)
                print(f"[EXTRACT] {num} ← {name} ({len(swf):,} bytes)")
            else:
                print(f"[FAIL]    {num} — no SWF found in {name}")
            continue

        print(f"[UNKNOWN] {num} — {name}")


if __name__ == "__main__":
    main()
