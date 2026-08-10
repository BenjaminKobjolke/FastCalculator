# Create a new release

Version source of truth is `version.txt` in the repo root. The `tools\`
scripts read and bump it; `pyproject.toml`'s `version` line is kept in sync
automatically by the increment/decrement scripts.

## One-command release (recommended)

```
tools\release_create.bat            # full release: notes, bump, translate, build, publish, commit, tag
tools\release_create.bat --internal # internal test build: skip notes, tag as INTERNAL
tools\release_create.bat --dry-run  # preview every step without changing anything
```

This runs the whole flow below via `release-tool create` in **semver** mode
(each release bumps the patch: `0.1.6` → `0.1.7`), configured by
`tools/release_create.ini`. After the build it **asks two questions**: whether to
run publish, and whether to commit + tag + push — decline either.

The previous (online) version for the publish backup is recorded automatically to
the gitignored `tools/previous_version.txt`; `publish_release.bat` reads it, so
`--previous-version` is never hand-edited (whether publish runs from
`release_create.bat` or you run `publish_release.bat` yourself later).

The manual steps below remain the reference for what happens under the hood.

## Steps

1. **Check the current version**

   ```
   tools\get_version.bat
   ```

2. **Increment the version**

   ```
   tools\increment_version.bat
   ```

   Bumps the patch number in **both** `version.txt` and `pyproject.toml`.
   Made a mistake? `tools\decrement_version.bat` undoes one step.

3. **Write the release notes** — create `release_notes\<version>\en.json`:

   ```json
   {
       "version": "0.1.1",
       "date": "2026-07-16",
       "notes": [
           "New: something added",
           "Fixed: something repaired",
           "Improved: something better"
       ]
   }
   ```

   | Field     | Meaning                                                    |
   |-----------|------------------------------------------------------------|
   | `version` | Must match the folder name (`X.Y.Z`).                      |
   | `date`    | Release date, `YYYY-MM-DD`.                                |
   | `notes`   | One entry per change, prefixed `New:` / `Fixed:` / `Improved:`. |

   Only write `en.json` by hand — the next step generates the other languages.

4. **Translate the release notes**

   ```
   tools\translator_release_notes.bat
   ```

   Runs the external GPT-json-translator over `release_notes\` and creates the
   other language files (`de.json`, …) next to each `en.json`. Do not skip —
   verify the language files appeared.

5. **Build**

   ```
   tools\build.bat
   ```

   PyInstaller onefile build → `dist\FastCalculator.exe` (or `%OUTPUT_PATH%`
   if `tools\compile_settings.bat` sets one; copy from the `.example`).
   Bundles `locales\`, `release_notes\` and `version.txt` into the exe, so
   `/help` and `/release-notes` work frozen.

6. **Publish**

   - `--previous-version` (the version currently online, for backup naming) is
     read from `tools\previous_version.txt` (written by `release_create.bat`).
     Pass an explicit arg to override: `tools\publish_release.bat 0.1.6` (empty →
     timestamped backup).
   - The exe is picked up automatically: `%OUTPUT_PATH%\FastCalculator.exe`
     when `tools\compile_settings.bat` sets one, else `dist\FastCalculator.exe`.
   - Requires a local `tools\publish_settings.ini` (gitignored) — copy
     `tools\publish_settings_example.ini` and fill in FTP credentials.

   ```
   tools\publish_release.bat
   ```

   The external release-tool signs the exe (network signing folder), uploads it
   via FTP, backs the old version up into a `versions/` subfolder, and uploads
   the `release_notes\` folders.

7. **Commit**

   ```
   RELEASE (calculator): X.Y.Z
   ```
