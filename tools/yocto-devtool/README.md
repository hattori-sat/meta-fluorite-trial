# Ubuntu 22.04 Devtool container

This image is for Mac-side Yocto patch preparation and recipe-scoped checks.
It must not run `bitbake agl-ivi-image-flutter`; the mini PC is the authoritative
image-build host.

The same Dockerfile is OCI-compatible for Podman. When a Podman machine is
available, build it once with `podman build -t fluorite-yocto-devtool:22.04
tools/yocto-devtool` and use `scripts/run-podman-devtool.sh`. The Podman wrapper
uses direct `podman create/start/exec` calls so `podman-compose` is not required.

## Persistent Compose lifecycle

Build the image once:

```sh
docker build --tag fluorite-yocto-devtool:22.04 tools/yocto-devtool
```

Run the host wrapper from the project root:

```sh
export FLUORITE_MAC_AGL_ROOT="$HOME/work/agl-trout-mac"
export FLUORITE_MAC_PROJECT_ROOT="$PWD"
scripts/run-mac-devtool.sh status
scripts/run-mac-devtool.sh modify flutter-auto
```

The first invocation creates the fixed `fluorite-mac-devtool` container. Later
invocations use `docker compose start` and `docker compose exec` against that
same container. The build, downloads, sstate-cache, and tmp directories are
fixed named volumes and are not recreated per ticket.

Inspect before any cleanup:

```sh
docker inspect fluorite-mac-devtool
docker volume ls --filter name=fluorite-mac-devtool
docker system df -v
```

Do not remove the named volumes as a routine step. Stop the container when it is
not needed; remove a volume only after explicit approval and confirmation that
no source workspace or evidence depends on it.

The AGL source is read-only and the project layer is mounted read-write. The
wrapper rejects known mini-PC paths, image recipes, and an existing container
whose labels do not match the requested mount/volume contract.

## Allowed commands

The container-side wrapper permits `devtool modify`, `devtool finish`,
`devtool status`, component-scoped `devtool reset --no-clean`, `devtool add`, and
`devtool update-recipe --mode patch --append --no-remove` (optionally with
`--force-patch-refresh`). It also permits
recipe-scoped parse/patch/compile/install/package tasks. Generated patches must
come from Devtool; do not hand-edit patch files.
