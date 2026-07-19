# Project layers

Project-owned Yocto layers live here. Generated build output, downloads, sstate, and deploy artifacts must not be copied into this directory.

`meta-local` is the sanitized build-host baseline, not a newly designed replacement layer. Preserve its recipe/appends and patch ordering until effective BitBake metadata and runtime evidence identify a specific problem point. In particular, do not infer that a package, Vulkan loader, or compile option proves the selected runtime device or successful presentation.
