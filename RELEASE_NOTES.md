# Scenario Builder 0.4.3

- Removes the fixed metadata research-round cutoff. Productive lookups can continue beyond the former limit.
- Detects repeated calls and identical results without new information, reuses cached lookups, and offers Continue or Revise with progress preserved.
- Saves complete metadata exchanges during research so an interrupted service can restore them. Stop, provider/format failures and actual context constraints still pause with saved progress.
- Retains main-chat review, explicit confirmation, local compiler validation, IFs baseline defaults and group-aware exports.

Requires **IFsCompanion 0.3.6 or newer**. Update Companion first, then update this optional tool through Manage tools. Saved scenarios are preserved. No confirmation or model-run approval is bypassed.
