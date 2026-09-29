# FLR-0369 selected guest runtime evidence

Run: `flr0369-0001` on the pinned current rootfs.

The following excerpts/counts were read over strict SSH from the guest log at
`/run/user/1001/flr0369-manual.log`. The full 26,956,638-byte log had SHA-256
`4d7655f29c7f69c738154289efa281264bfc66e0cdcb72f5121beae6e9dcf6fe`; it was
not copied into the repository. The guest `/run` log was ephemeral and is no
longer available after QEMU teardown.

```text
[15:53:34.866990] [I] FLUORITE_NATIVE_MATERIAL_BRANCH hardcoded=true shading=lit source=constant
[15:54:15.815972] [I] FLUORITE_NATIVE_FIXTURE_LIGHT_SETUP_DONE enabled=true type=SUN intensity=110000
[15:54:15.816170] [I] FLUORITE_NATIVE_MINIMAL_GEOMETRY_CONTRACT entity=12 has_renderable=true instance=2 primitives=1 bound_material=true material_instance=true vertex_count=8 index_count=36 scene=true
[15:54:15.824224] [I] FLUORITE_NATIVE_FIXTURE_CAMERA_FRAME_APPLIED eye=(0,0,5) target=(0,0,0)
```

Selected counts at the time the guest log was queried:

| Marker | Count |
| --- | ---: |
| `FLR0026_SCENE_STAGE_DRAW_SUBMIT` | 244 |
| `FLUORITE_VIEWTARGET_RENDER_RETURN` | 244 |
| `FLR0026_VK_PRESENT_BOUNDARY_DONE` | 242 |

The final selected tail was:

```text
[15:55:50.307238] [I] FLR0026_SCENE_STAGE_DRAW_SUBMIT scene_default=false scene_native=true swapchain=true view=true
[15:55:50.307961] [I] FLUORITE_VIEWTARGET_RENDER_RETURN
FLR0026_RENDERER_COMMIT_ENQUEUE
FLR0026_FRAME_FENCE_CREATE_REQUEST
FLR0026_FRAME_FENCE_CREATE_RETURNED valid=true
FLR0026_RENDERER_ENDFRAME_ENQUEUE
[15:55:50.308097] [I] FLR0026_SCENE_STAGE_DRAW_END
[15:55:50.308111] [I] FLUORITE_VIEWTARGET_END_FRAME
```

These excerpts show setup and draw/render activity but do not establish why
the app process later disappeared. No guest coredump/journal search was made
before the ephemeral VM was shut down; that exit cause remains UNKNOWN.
