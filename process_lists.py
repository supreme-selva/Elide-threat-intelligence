#!/usr/bin/env python3
"""
process_lists.py
================
Serverless DNS blocklist builder for the *network-ruleset-engine*.

It downloads a set of HaGeZi DNS blocklists (plain "Domains" syntax), tags
every domain with a category prefix, merges + deduplicates + sorts the result,
and writes it to ``final_blocklist.txt`` so an Android app can pull it straight
from GitHub's raw CDN.

Category prefixes
-----------------
    01  ->  Native OEM tracker domains (Xiaomi, Samsung, Huawei, Oppo/Realme,
            Vivo, Apple)
    02  ->  Ad / privacy domains (HaGeZi "Pro")

A domain that appears in both categories is emitted once per category (i.e.
both ``01 example.com`` and ``02 example.com``) so the app can keep independent
per-category toggles. Duplicates *within* a category are removed.

Source lists: HaGeZi's DNS Blocklists - https://github.com/hagezi/dns-blocklists
Licensed under GPL-3.0. This engine and its generated output are GPL-3.0 too.

Note on URLs
------------
HaGeZi serves the plain-domain lists from the ``wildcard/`` folder with the
``-onlydomains`` suffix. The older ``domains/`` path no longer exists and
returns HTTP 404, so these ``-onlydomains`` URLs are the verified sources.

Standard library only - no third-party dependencies.
"""

import os
import sys
import urllib.error
import urllib.request

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

_BASE = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard"

# Native OEM tracker lists -> tagged "01"
TRACKER_URLS = [
    f"{_BASE}/native.xiaomi-onlydomains.txt",
    f"{_BASE}/native.samsung-onlydomains.txt",
    f"{_BASE}/native.huawei-onlydomains.txt",
    f"{_BASE}/native.oppo-realme-onlydomains.txt",
    f"{_BASE}/native.vivo-onlydomains.txt",
    f"{_BASE}/native.apple-onlydomains.txt",
]

# Ad / privacy list -> tagged "02"
AD_URLS = [
    f"{_BASE}/pro-onlydomains.txt",
]

TRACKER_PREFIX = "01"
AD_PREFIX = "02"

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "final_blocklist.txt"
)

# GitHub raw can reject the default urllib User-Agent, so send an explicit one.
REQUEST_HEADERS = {"User-Agent": "network-ruleset-engine/1.0 (+https://github.com)"}
REQUEST_TIMEOUT = 60  # seconds


# --------------------------------------------------------------------------- #
# Core logic
# --------------------------------------------------------------------------- #

def download(url):
    """Download ``url`` and return its body decoded as UTF-8 text."""
    print(f"  -> Fetching {url}")
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def extract_domains(text):
    """Return a set of clean domains parsed from raw list ``text``.

    Blank lines and comment lines (starting with ``#``) are ignored.
    """
    domains = set()
    for line in text.splitlines():
        entry = line.strip()
        if not entry or entry.startswith("#"):
            continue
        domains.add(entry.lower())
    return domains


def collect(urls, label):
    """Download every URL in ``urls`` and return the merged set of domains."""
    print(f"Processing {label} lists ({len(urls)} source(s))...")
    merged = set()
    for url in urls:
        text = download(url)
        found = extract_domains(text)
        print(f"     {len(found):>8,} domains")
        merged |= found
    print(f"  {label} unique domains: {len(merged):,}\n")
    return merged


def build():
    """Fetch, tag, merge, sort and write the final blocklist."""
    print("=" * 62)
    print("network-ruleset-engine :: building final_blocklist.txt")
    print("=" * 62)

    tracker_domains = collect(TRACKER_URLS, "tracker (01)")
    ad_domains = collect(AD_URLS, "ad (02)")

    # Tag every domain with its category prefix. Using a set removes any
    # duplicate lines (same prefix + same domain).
    tagged = set()
    for domain in tracker_domains:
        tagged.add(f"{TRACKER_PREFIX} {domain}")
    for domain in ad_domains:
        tagged.add(f"{AD_PREFIX} {domain}")

    output = sorted(tagged)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(output))
        handle.write("\n")

    print("-" * 62)
    print(f"  01 tracker entries : {len(tracker_domains):>9,}")
    print(f"  02 ad entries      : {len(ad_domains):>9,}")
    print(f"  total lines written: {len(output):>9,}")
    print(f"  output file        : {OUTPUT_FILE}")
    print("-" * 62)
    print("Done.")


def main():
    try:
        build()
    except urllib.error.HTTPError as exc:
        print(f"ERROR: HTTP {exc.code} while fetching {exc.url}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"ERROR: network failure: {exc.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
