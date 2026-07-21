---
name: build-evo-converter
description: "Use when building a complete new Evo data converter from scratch, end to end. Orchestrates the four phases — scaffolding, discovery, mapping to Evo geoscience objects, and testing — for turning a third-party geoscience file format into published Evo objects. Use for: 'build a converter for X', 'add support for a new file format', 'create a new Evo importer', 'convert format X to Evo objects'. Start here, then follow the phase skills."
---

# Build an Evo data converter (end to end)

Orchestrates building a new converter that reads a third-party format, converts it to Evo
geoscience objects, and publishes them. Import-first; export is a documented follow-up. See
[`AGENTS.md`](../../../AGENTS.md) for repo-wide context and guardrails.

Work through the four phases in order, using the dedicated skill for each. Confirm the exit
criteria of each phase before moving on.

## Phase 1 — Scaffold

Skill: [`scaffold-converter`](../scaffold-converter/SKILL.md)

Run `uv run create-converter`, choose the converter type and import/export mode, `uv sync`, and
verify registration. The template generates `packages/<type>/tests/data/`; ask the user to drop
their sample file there. **Exit:** `packages/<type>/` exists, is registered in
Makefile/README/pyproject, `make test-<type>` passes on the placeholder stubs, and any sample
data is in `packages/<type>/tests/data/`.

## Phase 2 — Discovery

Skill: [`converter-discovery`](../converter-discovery/SKILL.md)

Inspect the sample data now sitting in `packages/<type>/tests/data/`, identify the input format,
choose a reader library (license-checked), and decide the target Evo object type(s). **Exit:** a
discovery summary with format, reader, intermediate representation, and target `evo_schemas`
object(s).

## Phase 3 — Map to Evo schemas

Skill: [`map-to-evo-schemas`](../map-to-evo-schemas/SKILL.md)

Implement `read_<type>_file` and `get_geoscience_object_from_<type>`; build the object, upload
referenced arrays, set bounding box/CRS/tags. **Exit:** `convert_<type>` produces a valid object
from a real sample (validated with `publish_objects=False`); `ruff` and `mypy` are clean.

## Phase 4 — Test

Skill: [`test-converter`](../test-converter/SKILL.md)

Replace placeholder tests with real ones, then run tests, lint, and type checks. **Exit:**
`make test-<type>`, `uv run ruff check`, and `uv run mypy packages/<type>` all pass.

## After import works

- **Export** (Evo → file): if scaffolded with "Import and Export", implement
  `export_<type>` / `export_blocksync_<type>` following the same reader/builder discipline in
  reverse; mirror `packages/omf`'s exporter.
- Update the package `README.md` and add a `code-samples` example for the new format.

## Guardrails

Never commit secrets or workspace details; stay within the `packages/<type>/` pattern; keep the
Apache 2.0 header; keep sample data small and appropriately licensed.
