---
id: "ADR-20260802-009"
title: "Optional Local-Backend Dependency Installer"
status: accepted
date: "2026-08-02"
module: "scripts/install-optional"
capability: "PLT-15"
owner: "platform"
decision-makers: [platform-engineering]
tags: [adr, architecture, install, dependencies, fresh-install]
---

# ADR-20260802-009: Optional Local-Backend Dependency Installer

## Status

accepted

## Date

2026-08-02

## Context

A fresh machine could install the core platform but had no documented way to install the heavy optional packages that unlock keyless local backends, so the fresh-install generation story was incomplete.

## Decision

Add `optional_requirements.txt` (8 dependency groups) and `scripts/install-optional.sh` (install-all, `--group`/`--groups`, `--dry-run`), documented in `setup.sh` and README.

## Consequences

### Positive

- One command unlocks all keyless CPU backends
- Group selection keeps installs lean


### Negative

- Heavy installs take time on slow machines


## Alternatives Considered

Bundle everything in requirements.txt (rejected: bloats mandatory install)

## Related

- [[Architecture Overview]]
- [[36-Generated/Modules/local_runtimes|local_runtimes]]
- Commits: `e7a0e21`

## Review History

| Date | Reviewer | Outcome |
|------|----------|---------|
| 2026-08-02 | Platform Engineering | accepted |
