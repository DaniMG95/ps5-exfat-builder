# Architecture

This project is moving from a single-file Tkinter application toward a
format-oriented desktop toolkit. The existing app remains available through
`exfat_builder.py`; new code should be added under `src/ps5_exfat_builder`.

## Current State

- `exfat_builder.py` contains the main Tkinter app, settings, metadata
  parsing, build queues, OSFMount flows, FTP, extraction, and conversion
  orchestration.
- `ui/` contains tab modules, but many tabs still import directly from
  `exfat_builder.py`.
- Tool integration is mixed into UI callbacks in several places.

This is workable for one application, but it is expensive to extend safely
when adding more target formats such as AMPR or PKG.

## Target Structure

```text
src/ps5_exfat_builder/
  app.py                  # Entrypoint and legacy bridge
  domain/                 # Pure models: formats, game metadata, requests
  formats/                # Converter contracts and format registry
  integrations/           # OSFMount, mkpfs, AMPR, PKG tool boundaries
  services/               # Progress, process, paths, workspace helpers
ui/                       # Existing Tkinter screens
exfat_builder.py          # Legacy application shell during migration
tests/                    # Core tests first, UI tests later
```

## Format Pipeline Model

Every conversion should become a registered route:

```text
source format -> converter backend -> target format
```

Examples:

- `folder -> exfat`
- `folder -> ffpkg`
- `exfat -> ffpkg`
- `ffpkg -> exfat`
- `exfat -> ffpfsc`
- `folder -> ampr`
- `exfat -> pkg`
- `ffpfsc -> pkg`

The UI should ask the registry what is available instead of hard-coding every
route in each tab. That allows new formats to appear in one place.

## External References

Lazy_AMPR is a useful reference because it separates `core`, `gui`, `tools`,
`utils`, TOML profiles, and tests. Its AMPR support should map to an AMPR
backend that handles:

- TOML profile discovery and selection.
- `ampr_emu`/packer execution.
- Folder-based workflows.
- Mounted exFAT read-only workflows.

The PS5 exFAT to PKG reference maps to a PKG backend that handles:

- exFAT image mounting.
- Temporary staging.
- PKG creation through the selected package builder.
- Optional SHA-256 verification.
- Firmware/SDK preset handling.

## Migration Rules

1. Keep `exfat_builder.py` runnable after every change.
2. Move pure code first: metadata parsing, path helpers, process wrappers,
   format detection, and command construction.
3. Keep Tkinter widgets in `ui/`; do not import Tkinter from `domain`,
   `formats`, `services`, or `integrations`.
4. Put third-party command execution behind `integrations/`.
5. Add tests for any code moved out of the monolith before wiring it back.

## Near-Term Migration Plan

1. Move game metadata parsing from `exfat_builder.py` to `domain/game_scan.py`.
   Status: done. The legacy functions now delegate to the package module.
2. Move OSFMount command construction and drive handling to
   `integrations/osfmount.py`.
3. Move `.exfat <-> .ffpkg` conversion workers behind registered converters.
4. Add `folder -> ampr` as a disabled backend until the AMPR tool path,
   TOML profile rules, and output layout are confirmed.
5. Add `exfat -> pkg` as a disabled backend until the PKG builder executable,
   SDK presets, staging policy, and verifier are confirmed.

## Implemented Core Modules

- `domain/game_scan.py`: SFO/param.json/nptitle metadata scanning, safe output
  naming, version normalization, and `.exfat` filename construction.
- `formats/registry.py`: supported format metadata and extension detection.
- `formats/routes.py`: declared transformation matrix, including legacy and
  planned routes.
- `integrations/osfmount.py`: OSFMount detection and mount/dismount command
  construction.
- `integrations/ufs2tool.py`: UFS2Tool `newfs` and `extract` command
  construction.
- `integrations/windows_volume.py`: Windows `format` and `robocopy` command
  construction.
- `integrations/ampr.py`: Lazy_AMPR TOML profile discovery, loading, and
  command construction for generic, route-flag, and positional backends.
- `integrations/pkg.py`: PKG builder input/tool contracts and a generic CLI
  adapter boundary.
- `services/file_inventory.py`: folder inventory and exFAT container sizing.
- `services/workspace.py`: temporary staging workspace lifecycle for converters.
- `services/process.py`: subprocess execution with optional high-performance
  hints for long-running conversion tools.

## Declared Routes

Legacy routes currently remain implemented by `exfat_builder.py` or `ui/`:

- `folder -> exfat`
- `folder -> ffpkg`
- `exfat -> ffpkg`
- `ffpkg -> exfat`
- `exfat -> ffpfsc`

Experimental routes are executable through registered converters:

- Any supported peer format to AMPR:
  `folder`, `exfat`, `ffpkg`, `ffpfs`, `ffpfsc`, `pkg`.
- AMPR to any supported peer format:
  `folder`, `exfat`, `ffpkg`, `ffpfs`, `ffpfsc`, `pkg`.
- `exfat -> pkg`
- `ffpfsc -> pkg`

AMPR is exposed through the Tkinter AMPR Studio tab and through the developer
CLI. The integration can discover common Lazy_AMPR launchers in a selected
directory, load TOML profiles, build route-aware command lines, and run the
external backend with optional high-priority/all-CPU process hints.

The high-performance mode does three things:

- Sets thread-count environment variables such as `OMP_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS`, and `PS5_EXFAT_WORKERS`.
- Attempts to pin the child process affinity to all logical CPUs when
  `psutil` supports it on the host.
- Attempts to raise the child process priority to high.

Actual CPU saturation still depends on the selected AMPR backend implementing
parallel work internally.

## Developer Inspection CLI

The package exposes a small CLI for inspecting the new core without launching
Tkinter:

```powershell
uv run ps5-exfat-builder-core formats
uv run ps5-exfat-builder-core routes
uv run ps5-exfat-builder-core ampr-dry-run --source game --target out.ampr --tool C:\Tools\Lazy_AMPR --profile C:\Tools\Lazy_AMPR\default.toml
uv run ps5-exfat-builder-core ampr-convert --source game --target out.ampr --tool C:\Tools\Lazy_AMPR --performance-preset max --worker-count 16
```
