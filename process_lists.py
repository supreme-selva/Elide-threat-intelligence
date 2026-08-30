#!/usr/bin/env python3
"""
process_lists.py
================
Serverless DNS blocklist builder for the *network-ruleset-engine*
(repository: Elide-threat-intelligence).

It downloads a set of tracker blocklists and a set of ad blocklists, computes
their intersection, tags every domain with a category prefix based on set
membership, sorts the result, and writes it to ``final_blocklist.txt`` so an
Android app can pull it straight from GitHub's raw CDN.

Set operations
--------------
    set_trackers   = union of every TRACKER_URLS list
    set_ads        = union of every AD_URLS list
    set_both       = set_trackers ∩ set_ads      -> prefix "03"
    pure_trackers  = set_trackers - set_both      -> prefix "01"
    pure_ads       = set_ads - set_both           -> prefix "02"

Every domain therefore lands in exactly one category, so no domain is emitted
more than once.

Category prefixes
-----------------
    01  ->  pure trackers (only in the tracker lists)
    02  ->  pure ads      (only in the ad lists)
    03  ->  both          (present in a tracker list AND an ad list)

Sources
-------
    Trackers : Firebog EasyPrivacy + HaGeZi native OEM tracker lists
    Ads      : HaGeZi "Pro"

Note on URLs
------------
HaGeZi serves the plain-domain lists from the ``wildcard/`` folder with the
``-onlydomains`` suffix. The older ``domains/`` path no longer exists and
returns HTTP 404, so these ``-onlydomains`` URLs are the verified sources.

Licensing
---------
Source lists are GPL-3.0 (HaGeZi) and GPL-3.0 (EasyPrivacy via Firebog). This
engine and its generated output are distributed under GPL-3.0 as well.

Standard library only - no third-party dependencies.
"""

import os
import sys
import urllib.error
import urllib.request

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

_HAGEZI = "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard"

# Tracker lists -> categorised as "01" (unless also present in the ad set).
TRACKER_URLS = [
    "https://v.firebog.net/hosts/Easyprivacy.txt",
    f"{_HAGEZI}/native.apple-onlydomains.txt",
    f"{_HAGEZI}/native.huawei-onlydomains.txt",
    f"{_HAGEZI}/native.oppo-realme-onlydomains.txt",
    f"{_HAGEZI}/native.samsung-onlydomains.txt",
    f"{_HAGEZI}/native.vivo-onlydomains.txt",
    f"{_HAGEZI}/native.xiaomi-onlydomains.txt",
]

# Ad lists -> categorised as "02" (unless also present in the tracker set).
AD_URLS = [
    f"{_HAGEZI}/pro-onlydomains.txt",
]

TRACKER_PREFIX = "01"  # pure trackers
AD_PREFIX = "02"       # pure ads
BOTH_PREFIX = "03"     # present in both sets

OUTPUT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "final_blocklist.txt"
)

# GitHub raw / Firebog can reject the default urllib User-Agent, so send our own.
REQUEST_HEADERS = {"User-Agent": "network-ruleset-engine/1.0 (+https://github.com)"}
REQUEST_TIMEOUT = 60  # seconds

# Hosts-file noise to ignore. Lines like "0.0.0.0 example.com" are reduced to
# the domain; bare localhost/loopback entries are dropped entirely.
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

def download(url):
    """Download ``url`` and return its body decoded as UTF-8 text."""
    print(f"  -> Fetching {url}")
    request = urllib.request.Request(url, headers=REQUEST_HEADERS)
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw = response.read()
    return raw.decode("utf-8", errors="replace")


def parse_domains(text):
    """Return a set of clean, lowercased domains parsed from raw list ``text``.

    Ignores blank lines, comment lines (``#``), and localhost/loopback noise.
    Handles both plain "domain" and hosts-style "0.0.0.0 domain" lines.
    """
    domains = set()
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


def collect(urls, label):
    """Download every URL in ``urls`` and return the merged set of domains."""
    print(f"Processing {label} lists ({len(urls)} source(s))...")
    merged = set()
    for url in urls:
        text = download(url)
        found = parse_domains(text)
        print(f"     {len(found):>8,} domains")
        merged |= found
    print(f"  {label} unique domains: {len(merged):,}\n")
    return merged


def build():
    """Fetch, apply set operations, tag, sort and write the final blocklist."""
    print("=" * 62)
    print("network-ruleset-engine :: building final_blocklist.txt")
    print("=" * 62)

    set_trackers = collect(TRACKER_URLS, "tracker")
    set_ads = collect(AD_URLS, "ad")

    # Set operations.
    set_both = set_trackers & set_ads
    pure_trackers = set_trackers - set_both
    pure_ads = set_ads - set_both

    # Tag each domain by category. Every domain is in exactly one bucket.
    tagged = set()
    tagged.update(f"{TRACKER_PREFIX} {domain}" for domain in pure_trackers)
    tagged.update(f"{AD_PREFIX} {domain}" for domain in pure_ads)
    tagged.update(f"{BOTH_PREFIX} {domain}" for domain in set_both)

    output = sorted(tagged)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(output))
        handle.write("\n")

    print("-" * 62)
    print(f"  01 pure trackers : {len(pure_trackers):>9,}")
    print(f"  02 pure ads      : {len(pure_ads):>9,}")
    print(f"  03 in both sets  : {len(set_both):>9,}")
    print(f"  total written    : {len(output):>9,}")
    print(f"  output file      : {OUTPUT_FILE}")
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
