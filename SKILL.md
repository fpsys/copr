---
name: copr-recipe-maintenance
description: Use when a COPR build fails, an upstream release breaks update.py or the RPM spec, or when adding a new package recipe to this repository
---

# COPR Recipe Maintenance

## Repository Layout

```text
.github/workflows/check-upstream.yml   # Discovers recipes/*/, commits updates, submits COPR SCM builds
recipes/
  <name>/
    <name>.spec                        # RPM spec (uses %autorelease + %changelog / %autochangelog)
    update.py                          # Upstream release checker & spec updater
```

Each recipe is self-contained under `recipes/<name>/`. The workflow loops over `recipes/*/`, runs `update.py`, commits any changed `<name>.spec`, and runs `copr-cli buildscm --subdir "recipes/<name>" --spec "<name>.spec"`.

## Non-Negotiable Spec & Updater Invariants

1. **Always keep `%changelog` above `%autochangelog`**:
   ```spec
   %changelog
   %autochangelog
   ```
   `%autochangelog` expands only to changelog entries, not the section header. Omitting `%changelog` leaves `rpmbuild` inside `%files` when `%autochangelog` expands, failing with `error: File must begin with "/": *`.
2. **Keep `Release: %autorelease`** and never let `update.py` modify `Release:` or `%changelog` / `%autochangelog`.
3. **Resolve spec path relative to `update.py`**:
   ```python
   SPEC = Path(__file__).resolve().parent / "<name>.spec"
   ```
4. **Use `[ \t]*$` (not `\s*$`)** in `re.MULTILINE` substitutions in `update.py` so blank lines between spec sections (`%autosetup` -> `%build`) are preserved.

## Diagnosing a Broken COPR Build

1. **Fetch the full COPR build log** (user-pasted logs are often truncated before the actual error):
   ```bash
   curl -fsSL "https://download.copr.fedorainfracloud.org/results/<owner>/<project>/<chroot>/<build_id>-<pkg>/builder-live.log.gz" | gunzip | tail -n 120
   ```
2. **Inspect the upstream release archive** without guessing file paths:
   - List archive members and read `CMakeLists.txt` / `install.sh` directly from the GitHub release `.tar.gz`.
   - For `kiri`: check `effect-cpp/CMakeLists.txt`, `effect-cpp/*/CMakeLists.txt`, and `install.sh` (`dep_hint` for dependencies, installed plugins/shaders/desktop files).
3. **Match the failure to its cause**:
   - `Installed (but unpackaged) file(s) found` or `File not found`: update `%files` and `%check` in `recipes/<name>/<name>.spec`.
   - `Could not update ...` or `Release archive is missing required ...` in `update.py`: upstream changed archive root/asset naming or file layout; update `required` paths or regexes in `recipes/<name>/update.py`.
   - C++ compile / CMake failure on newer Fedora (e.g., KWin ABI bump): check `KWin_VERSION` handling in upstream `effect-cpp/CMakeLists.txt` and `BuildRequires` in `<name>.spec`.
   - `File must begin with "/": *`: `%changelog` header is missing above `%autochangelog`.

## Adding a New Recipe

1. Create `recipes/<pkg>/<pkg>.spec` with `Release: %autorelease`, `%check`, and `%changelog\n%autochangelog`.
2. Create `recipes/<pkg>/update.py` (modeled on `recipes/kiri/update.py`) that:
   - Exits `0` with no changes when already on the latest upstream version.
   - Validates the downloaded archive before editing `<pkg>.spec`.
   - Updates only `Version:`, `Source0:`, checksum verification, and `%autosetup -n ...`.
3. Verify `python3 -m py_compile recipes/<pkg>/update.py` and check `check-upstream.yml` discovers `recipes/<pkg>/`.
