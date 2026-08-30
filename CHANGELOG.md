# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the daily data refreshes are handled automatically by CI (commit message
`Automated blocklist update`) and are not listed individually.

## [Unreleased]

### Added
- Professional project documentation: overhauled `README.md` with badges, an
  architecture diagram, and a project map.
- Community & hygiene files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, `CHANGELOG.md`, `.editorconfig`, and `.gitignore`.
- GitHub issue and pull request templates.
- CI hardening: concurrency guard, per-run timeout, a path-filtered push
  trigger, and a live job summary of category counts.

### Changed
- `process_lists.py` refactored with type hints and a job-summary writer; the
  `final_blocklist.txt` output format is unchanged.

## [0.2.0]

### Added
- Firebog **EasyPrivacy** as an additional tracker source.
- Three-way set-intersection classification:
  - `01` pure trackers, `02` pure ads, `03` present in both sets.
- Localhost/hosts-format-aware parsing.

## [0.1.0]

### Added
- Initial serverless engine: fetches HaGeZi native OEM tracker lists and the
  HaGeZi Pro ad list, tags domains, and publishes `final_blocklist.txt`.
- Daily GitHub Actions workflow with auto-commit.
- GPL-3.0 license and upstream attribution.
