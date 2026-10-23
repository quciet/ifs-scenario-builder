# Scenario Builder maintenance

- Source belongs here; Companion owns its engine, shared Python runtime, AI settings, and installation validation helpers.
- Use scripts/build_tool.py and scripts/test.py. Set IFS_COMPANION_PATH for a non-sibling Companion checkout.
- Keep tool ID ifs-scenario-builder and existing data paths stable. Source relocation must not migrate or delete user data.
- Official release assets remain in quciet/ifs-companion, like the other tools. Use a new version for changed packages; never replace published assets.
- Build/test staging must use TemporaryDirectory or try/finally cleanup. Do not retain copied runtimes or installed test apps.
- After a successful published build, verify the package and SHA256 before removing recognized older local release packages and their checksum/metadata files. Preserve prior releases on failure.
- Never sweep output/, data/, build/, or dist/. Inspect exact cleanup targets, reject links, and preserve saved scenarios, settings, and unknown user files. Never stop another task's processes for cleanup.
