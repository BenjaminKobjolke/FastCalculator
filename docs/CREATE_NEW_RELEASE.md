# Create a new release

Version source of truth is `version.txt` in the repo root. The `tools\`
scripts read and bump it; `pyproject.toml`'s `version` line is kept in sync
automatically by the increment/decrement scripts.

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

   - Edit `tools\publish_release.bat`: set `--previous-version` to the version
     you are replacing (the one currently online).
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
