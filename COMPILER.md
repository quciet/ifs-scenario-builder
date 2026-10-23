# Scenario compiler

Local compiler and notebook API; no network calls or third-party dependencies.

The selected installation is authoritative:

- Parameter dimensions: `RUNFILES/IFsVar.db`, table `IFsVar`.
- Subgroup indices: `DATA/IFS.grp`.
- Country spellings: `DATA/IFs.db`, table `RegionIDNewFull`, column `RegionName`.

Scenario Builder resolves the shared installation for every `/api/scenario/references`
request. SQLite connections use read-only mode. Missing references or invalid
schemas halt loading; there is no fallback to older documentation snapshots.

The native references in `../Docs/Gem-Jonathan` are supported and covered by an
integration test: 1,863 dictionary entries, 57 subgroup dimensions, and 188 country
names. `IFsVar.txt` is CSV; uppercase computed variables are retained in the
dictionary but rejected as scenario parameter requests. `IFS.grp` starts with the
maximum dimension ID (58), followed by dimensions 2 through 58. Each row starts
with a member count and then ordered names with indices beginning at 1. This
mapping was checked against the native loader in
`IFs-Dev/src/IFs.Cli/IFsFunctions.vb`.

The loader also accepts reviewed CSV/TSV exports with these headers:

- Variables: `NAME,DIMENSION1,DIMENSION2,DIMENSION3`. NAME must be exact lowercase.
- Groups: `DIMENSION,INDEX,NAME`. Each group member must have its actual dimension
  flag and integer index from IFS.grp; no generated indices.
- Countries: exact names, one per line, without a header.

Do not rename or restructure originals without reviewing their formats. Unsupported
reference layouts halt with an error. The parser supports UTF-8 with optional BOM.

## Notebook / IDE usage

Add this directory to your Python import path, then:

```python
from pathlib import Path
from scenario_compiler import Compiler, References

work = Path(r'D:\your\operational\directory')
settings_file = Path(r'D:\path\to\Companion\data\settings.json')
refs = References.from_companion_settings(settings_file)
compiler = Compiler(refs, base_year=2022)
# entries must contain real dictionary parameter names and validated targets.
# values begin at base_year and specify every sequential year explicitly.
rows = compiler.build(entries)
metadata = dict(purpose='Describe the approved scenario purpose.',
                regeneration_prompt='State the final approved parameters, targets, years and rules.',
                model_context={'version': 'actual IFs version', 'base_year': 2022})
output = compiler.save(rows, work / 'NewScenario.sce', **metadata)

rows = compiler.read(work / 'BaseWar4.sce')
# changes: parameter, targets, start_year, end_year, operation, optional value.
# operation is multiply, add, or zero. Year boundaries are inclusive.
changed = compiler.modify(rows, changes)
output = compiler.save(changed, work / 'BaseWar4_flavor.sce', **metadata)
```

`targets` lists active dimensions in order. Dimension 1 flag 1 uses the exact
country spelling. All other active dimensions accept validated integer indices
or exact subgroup names; names are resolved to native indices before writing.
No missing targets, years, values, or parameters are inferred. Decimal arithmetic
avoids binary floating point rounding. Changes run in order and may overlap.
Unknown parameters, invalid indices, duplicate targets, nonfinite values, missing
rows, and out-of-range years halt compilation. Existing non-CUSTOM CSV records
are preserved semantically; CSV quoting and line endings are normalized. Everything
after COMMENT,START is preserved as plain text, including commas and quotes.

## Command line

Run `python scenario_compiler.py job.json`. The JSON object contains:

- `companion_settings`: path to the active Companion data folder's `settings.json`.
- `base_year`: optional, defaults to 2022.
- `output`: a new `.sce` path.
- `entries`: objects with `parameter`, `targets`, and `values` for creation.
- Or `source` and `changes` for modifying a scenario.

Relative paths resolve beside the JSON job. Absolute paths are also accepted.
Validation completes before export. Keep source files and generated flavors in
your chosen operational directory.

Run checks with `python scripts/test.py` from this folder.
Tests cover synthetic dimensional cases and real reference loading, subgroup
mapping, export, re-read, and modification. Execution by the IFs model itself
has not been tested, and no existing user scenario has been modified.

## Mandatory descriptive generation record

Every compiler export ends with COMMENT,START and a readable generation record:
a UTC creation timestamp with timezone, general purpose, exact parameter names,
refined regeneration prompt, IFs version, base year, and source filename (or New
scenario). Purpose, prompt, and model context are mandatory save/CLI inputs.

Describe the intent and mechanism in prose. For example: increase Iraq's baseline
agricultural yield multiplier to twofold by 2100 through parameter ylm, using a
linear increase from the model base year. The purpose and regeneration prompt
must reflect the final approved changes and name the relevant parameters.
The compiler also automatically lists the exact parameter names used in the file.

Do not include a structured specification, annual value arrays, JSON, or a duplicate
numeric trajectory in the generated comments. Natural descriptions of targets,
timeframes, and methods are appropriate. The numerical scenario rows are the
source for exact annual values; comments explain their intended meaning.

Existing source comments and prior generation records are retained as plain text
before the new generation record under the single trailing comment marker.
CLI jobs require purpose, regeneration_prompt, and model_context (version and
base_year). This is enforced for notebook usage as well as CLI exports.
