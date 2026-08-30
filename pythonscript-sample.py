"""
combine_lists.py
Combines adblock.txt and trackerslist.txt into list.txt with prefixes:
  01 - domain only in trackerslist.txt
  02 - domain only in adblock.txt
  03 - domain in both lists
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADBLOCK_FILE   = os.path.join(BASE_DIR, "adblock.txt")
TRACKERS_FILE  = os.path.join(BASE_DIR, "trackerslist.txt")
OUTPUT_FILE    = os.path.join(BASE_DIR, "list.txt")


def load_domains(filepath, strip_suffix="^"):
    """Read a domain list file and return a set of cleaned domains."""
    domains = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if not domain or domain.startswith("#"):
                continue
            if strip_suffix and domain.endswith(strip_suffix):
                domain = domain[: -len(strip_suffix)]
            domain = domain.strip()
            if domain:
                domains.add(domain.lower())
    return domains


def main():
    print("Loading lists...")
    adblock_domains  = load_domains(ADBLOCK_FILE,  strip_suffix="^")
    tracker_domains  = load_domains(TRACKERS_FILE, strip_suffix="")

    only_trackers = tracker_domains - adblock_domains   # 01
    only_adblock  = adblock_domains  - tracker_domains  # 02
    in_both       = tracker_domains  & adblock_domains  # 03

    lines = []

    for domain in sorted(only_trackers):
        lines.append(f"01 {domain}")

    for domain in sorted(only_adblock):
        lines.append(f"02 {domain}")

    for domain in sorted(in_both):
        lines.append(f"03 {domain}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Done!")
    print(f"  01 (trackers only) : {len(only_trackers):>8,}")
    print(f"  02 (adblock only)  : {len(only_adblock):>8,}")
    print(f"  03 (both)          : {len(in_both):>8,}")
    print(f"  Total              : {len(lines):>8,}")
    print(f"  Saved to           : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
