# Elide-threat-intelligence

A serverless, fully automated DNS blocklist engine powered by GitHub Actions.

Every day a scheduled workflow fetches several upstream tracker and ad blocklists ([HaGeZi DNS blocklists](https://github.com/hagezi/dns-blocklists) and [Firebog EasyPrivacy](https://firebog.net/)), computes their set intersection, tags each domain with a category prefix, sorts the result, and commits a single `final_blocklist.txt` back to this repository. Client apps can then download the merged list directly over GitHub's raw CDN, no server required.

## How it works

1. **`process_lists.py`** downloads the source lists using the Python standard library (`urllib`), skips blank/comment/localhost lines, computes the set intersection between trackers and ads, prefixes each domain by category, sorts, and writes `final_blocklist.txt`.
2. **`.github/workflows/update.yml`** runs the script on a daily cron (`02:00 UTC`, plus manual `workflow_dispatch`) and commits any changes.
3. Your app downloads the raw file and applies the rules.

## Set logic

Domains are bucketed by set membership, so each domain appears exactly once:

```
set_trackers  = union of all tracker lists
set_ads       = union of all ad lists
set_both      = set_trackers ∩ set_ads      -> 03
pure_trackers = set_trackers - set_both      -> 01
pure_ads      = set_ads - set_both           -> 02
```

## Output format

`final_blocklist.txt` contains one entry per line, each prefixed with a two-digit category tag:

```
01 tracker.example.com
02 ads.example.net
03 tracker-and-ad.example.org
```

| Prefix | Category | Meaning |
| ------ | ---------------- | ---------------------------------------------------------- |
| `01`   | Pure trackers    | Present only in the tracker lists                          |
| `02`   | Pure ads         | Present only in the ad lists                               |
| `03`   | Both             | Present in a tracker list **and** an ad list (intersection)|

## Consuming the list

Download the latest merged list from the raw CDN:

```
https://raw.githubusercontent.com/supreme-selva/Elide-threat-intelligence/main/final_blocklist.txt
```

## Running locally

Requires Python 3.10+ (standard library only, no dependencies):

```bash
python process_lists.py
```

This regenerates `final_blocklist.txt` in the repository root and prints the count of pure trackers (`01`), pure ads (`02`), and domains in both (`03`).

## Sources

**Trackers**

- [Firebog EasyPrivacy](https://v.firebog.net/hosts/Easyprivacy.txt) (derived from EasyList's EasyPrivacy)
- HaGeZi native OEM tracker lists (`wildcard/*-onlydomains.txt`): `native.apple`, `native.huawei`, `native.oppo-realme`, `native.samsung`, `native.vivo`, `native.xiaomi`

**Ads**

- HaGeZi `pro` list (`wildcard/pro-onlydomains.txt`)

The HaGeZi lists use the plain "Domains (without subdomains)" syntax served from the `wildcard/` folder with the `-onlydomains` suffix.

## Data Source & Attribution

The blocklists generated in this repository are modified derivatives of the [HaGeZi DNS Blocklists](https://github.com/hagezi/dns-blocklists) and the [EasyPrivacy](https://easylist.to/) list (mirrored and parsed by [Firebog](https://firebog.net/)), both licensed under the GPL-3.0 License. This repository and its outputs are distributed under the same GPL-3.0 License.

## License

This project is licensed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) for the full text.
