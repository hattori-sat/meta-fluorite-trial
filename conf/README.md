# Build configuration templates

Configuration snapshots are sanitized templates captured from the fixed baseline. `@AGL_ROOT@` and `@AGL_BUILD_DIR@` are role placeholders; do not commit their resolved host values.

Use `scripts/materialize-build-conf.sh` from the repository root. It defaults to a dry run and refuses to overwrite an existing `local.conf` or `bblayers.conf`. These snapshots are input evidence, not proof that BitBake has resolved the expected values on another host.
