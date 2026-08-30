# Elide-threat-intelligence

A serverless, fully automated DNS blocklist engine powered by GitHub Actions.

Every day a scheduled workflow fetches several upstream [HaGeZi DNS blocklists](https://github.com/hagezi/dns-blocklists), tags each domain with a category prefix, merges and deduplicates them, sorts the result, and commits a single `final_blocklist.txt` back to this repository. Client apps can then download the merged list directly over GitHub's raw CDN, no server required.

## How it works

1. **`process_lists.py`** downloads the source lists using the Python standard library (`urllib`), skips blank/comment lines, prefixes each domain by category, deduplicates, sorts, and writes `final_blocklist.txt`.
2. **`.github/workflows/update.yml`** runs the script on a daily cron (`02:00 UTC`, plus manual `workflow_dispatch`) and commits any changes.
3. Your app downloads the raw file and applies the rules.

## Output format

`final_blocklist.txt` contains one entry per line, each prefixed with a two-digit category tag:

```
01 tracker.example.com
02 ads.example.net
```

| Prefix | Category | Source |
| ------ | ------------------------------- | ------------------------------------------------------ |
| `01`   | Native OEM tracker domains      | HaGeZi `native.*` lists (Xiaomi, Samsung, Huawei, Oppo/Realme, Vivo, Apple) |
| `02`   | Ad / privacy domains            | HaGeZi `pro` list                                      |

A domain present in both categories appears once per category (both `01 <domain>` and `02 <domain>`), so an app can offer independent per-category toggles. Duplicates within a category are removed.

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

This regenerates `final_blocklist.txt` in the repository root.

## Sources

The upstream domain lists are pulled from HaGeZi's `wildcard/*-onlydomains.txt` files, which use the plain "Domains (without subdomains)" syntax:

- `native.xiaomi-onlydomains.txt`
- `native.samsung-onlydomains.txt`
- `native.huawei-onlydomains.txt`
- `native.oppo-realme-onlydomains.txt`
- `native.vivo-onlydomains.txt`
- `native.apple-onlydomains.txt`
- `pro-onlydomains.txt`

## Data Source & Attribution

The blocklists generated in this repository are modified derivatives of the HaGeZi DNS Blocklists (https://github.com/hagezi/dns-blocklists), licensed under the GPL-3.0 License. This repository and its outputs are distributed under the same GPL-3.0 License.

## License

This project is licensed under the **GNU General Public License v3.0**. See [`LICENSE`](LICENSE) for the full text.
