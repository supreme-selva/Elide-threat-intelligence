#!/usr/bin/env python3
"""Elide Threat Intelligence — DNS blocklist build engine.

Downloads a set of tracker blocklists and a set of ad blocklists, computes
their intersection, tags every domain by set membership, sorts the result, and
writes it to ``final_blocklist.txt`` for distribution over GitHub's raw CDN.

Set operations
--------------
    set_trackers   = union of every TRACKER_URLS list
    set_ads        = union of every AD_URLS list
    set_both       = set_trackers & set_ads       -> prefix "03"
    pure_trackers  = set_trackers - set_both       -> prefix "01"
    pure_ads       = set_ads - set_both            -> prefix "02"

Every domain lands in exactly one category, so no domain is emitted twice.

Output format (stable — downstream apps depend on it)
-----------------------------------------------------
    UTF-8, LF line endings, sorted, one entry per line: ``<tag> <domain>``.

Sources
-------
    Trackers : Firebog EasyPrivacy + HaGeZi native OEM tracker lists
    Ads      : HaGeZi "Pro"

    HaGeZi serves the plain-domain lists from the ``wildcard/`` folder with the
    ``-onlydomains`` suffix; the older ``domains/`` path returns HTTP 404.

Licensing
---------
    Source lists are GPL-3.0 (HaGeZi) and GPL-3.0 (EasyPrivacy via Firebog).
    This engine and its output are distributed under GPL-3.0 as well.

Standard library only — no third-party dependencies.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

_HAGEZI = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard"

#: Tracker sources — categorised "01" unless also present in the ad set.
TRACKER_URLS: list[str] = [
    "https://v.firebog.net/hosts/Easyprivacy.txt",
    f"{_HAGEZI}/native.apple-onlydomains.txt",
    f"{_HAGEZI}/native.huawei-onlydomains.txt",
    f"{_HAGEZI}/native.oppo-realme-onlydomains.txt",
    f"{_HAGEZI}/native.samsung-onlydomains.txt",
    f"{_HAGEZI}/native.vivo-onlydomains.txt",
    f"{_HAGEZI}/native.xiaomi-onlydomains.txt",
]

#: Ad sources — categorised "02" unless also present in the tracker set.
AD_URLS: list[str] = [
    f"{_HAGEZI}/pro-onlydomains.txt",
]

TRACKER_PREFIX = "01"  # pure trackers
AD_PREFIX = "02"       # pure ads
BOTH_PREFIX = "03"     # present in both sets

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "final_blocklist.txt"
)

# GitHub raw / Firebog can reject the default urllib User-Agent, so send our own.
REQUEST_HEADERS = {"User-Agent": "elide-threat-intelligence/1.0 (+https://github.com)"}
REQUEST_TIMEOUT = 60  # seconds

# Hosts-file noise. Lines like "0.0.0.0 example.com" are reduced to the domain;
# bare localhost/loopback entries are dropped entirely.
_IP_PREFIXES = {"0.0.0.0", "127.0.0.1", "::1", "255.255.255.255", "fe80::1", "ff02::1", "ff02::2"}
_SKIP_TOKENS = {
    "localhost",
    "localhost.localdomain",
    "local",
    "broadcasthost",
    "ip6-localhost",
    "ip6-loopback",
    "ip6-allnodes",
    "ip6-allrouters",
}


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #

def download(url: str) -> str:
    """Download ``url`` and return its body decoded as UTF-8 text."""
    print(f"  -> Fetching {url}")
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def parse_domains(text: str) -> set[str]:
    """Return a set of clean, lowercased domains parsed from raw list ``text``.

    Ignores blank lines, comment lines (``#``), and localhost/loopback noise.
    Handles both plain "domain" and hosts-style "0.0.0.0 domain" lines.
    """
    domains: set[str] = set()
    for line in text.splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue

        # Hosts format: strip a leading IP token ("0.0.0.0 domain").
        parts = entry.split()
        if len(parts) >= 2 and parts[0] in _IP_PREFIXES:
            entry = parts[1]

        entry = entry.strip().lower()
        if not entry or entry in _SKIP_TOKENS or entry in _IP_PREFIXES:
            continue

        domains.add(entry)
    return domains


def collect(urls: list[str], label: str) -> set[str]:
    """Download every URL in ``urls`` and return the merged set of domains."""
    print(f"Processing {label} lists ({len(urls)} source(s))...")
    merged: set[str] = set()
    for url in urls:
        found = parse_domains(download(url))
        print(f"     {len(found):>8,} domains")
        merged |= found
    print(f"  {label} unique domains: {len(merged):,}\n")
    return merged


def build() -> dict[str, int]:
    """Fetch, apply set operations, tag, sort and write the final blocklist.

    Returns a dict of counts for logging and the CI job summary.
    """
    print("=" * 62)
    print("elide-threat-intelligence :: building final_blocklist.txt")
    print("=" * 62)

    set_trackers = collect(TRACKER_URLS, "tracker")
    set_ads = collect(AD_URLS, "ad")

    # Set operations — each domain ends up in exactly one bucket.
    set_both = set_trackers & set_ads
    pure_trackers = set_trackers - set_both
    pure_ads = set_ads - set_both

    tagged: set[str] = set()
    tagged.update(f"{TRACKER_PREFIX} {domain}" for domain in pure_trackers)
    tagged.update(f"{AD_PREFIX} {domain}" for domain in pure_ads)
    tagged.update(f"{BOTH_PREFIX} {domain}" for domain in set_both)

    output = sorted(tagged)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(output))
        handle.write("\n")

    counts = {
        "trackers": len(set_trackers),
        "ads": len(set_ads),
        "pure_trackers": len(pure_trackers),
        "pure_ads": len(pure_ads),
        "both": len(set_both),
        "total": len(output),
    }

    print("-" * 62)
    print(f"  01 pure trackers : {counts['pure_trackers']:>9,}")
    print(f"  02 pure ads      : {counts['pure_ads']:>9,}")
    print(f"  03 in both sets  : {counts['both']:>9,}")
    print(f"  total written    : {counts['total']:>9,}")
    print(f"  output file      : {OUTPUT_FILE}")
    print("-" * 62)
    print("Done.")
    return counts


def write_job_summary(counts: dict[str, int]) -> None:
    """Write a Markdown build summary to the GitHub Actions run, if available.

    No-op outside CI (when ``GITHUB_STEP_SUMMARY`` is unset).
    """
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    rows = [
        "## Blocklist build summary",
        "",
        "| Category | Tag | Domains |",
        "| :--- | :---: | ---: |",
        f"| Pure trackers | `01` | {counts['pure_trackers']:,} |",
        f"| Pure ads | `02` | {counts['pure_ads']:,} |",
        f"| Both (intersection) | `03` | {counts['both']:,} |",
        f"| **Total** | | **{counts['total']:,}** |",
        "",
        f"Tracker set: **{counts['trackers']:,}** unique · "
        f"Ad set: **{counts['ads']:,}** unique",
        "",
    ]
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + "\n")


def main() -> None:
    try:
        counts = build()
        write_job_summary(counts)
    except urllib.error.HTTPError as exc:
        print(f"ERROR: HTTP {exc.code} while fetching {exc.url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"ERROR: network failure: {exc.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
