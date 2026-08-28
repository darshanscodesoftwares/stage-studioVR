# Asset credits and licences

**Nothing here yet, and as of M0 that is a deliberate position rather than an
oversight.** The hall ships zero downloaded assets: every texture is generated
at runtime on a canvas, and all geometry is A-Frame primitives. The only
third-party code is A-Frame 1.7.0 itself, from its CDN, under the MIT licence.

That means M0 is **clear to deploy publicly**, which is precisely what
room-studioVR cannot do. Keep it that way for as long as possible — the moment
the audience arrives, so does the licence problem.

Add an entry the moment an asset enters `assets/` — before converting it, not
after.

room-studioVR skipped this step and ended up with figures whose licence
forbids redistributing the 3D data, baked into the scene. A public URL is
redistribution. That project cannot be deployed publicly as a result.

Every entry needs:

- **What it is** and the source pack name
- **Author / vendor**
- **Licence**, quoted, and where it was found — "unknown" is a status that
  blocks deploy, not a footnote
- **Processing applied** — conversion tool, texture downsizing, channel
  swaps, anything stripped

Prefer CC0. [Poly Haven](https://polyhaven.com) is CC0 throughout.
[Freesound](https://freesound.org) can be filtered to CC0 for audio.
[Sketchfab](https://sketchfab.com) can be filtered to CC0/CC-BY, but the
licence is per-model and must be checked every time.

---

## `chair.glb` — auditorium seating

- **What it is:** School Chair 01, from the Poly Haven CC0 model library.
  Used as the auditorium seat, instanced across the whole house.
- **Author / vendor:** Ethan Place, via [Poly Haven](https://polyhaven.com/a/SchoolChair_01).
- **Licence:** **CC0.** Poly Haven's licence page states it plainly: *"Our assets
  are all licensed as CC0, which is effectively Public Domain even in
  jurisdictions that do not support the Public Domain... You can use our assets
  for any purpose, including commercial work. You do not need to give credit or
  attribution when using them (although it is appreciated). You can redistribute
  them, share them around, include them when sharing your own work."*
  Retrieved from <https://polyhaven.com/license>. Credited here anyway.
- **Source form:** glTF, 1k textures — 5,072 triangles, 0.46 MB
  (bin 132 KB, diffuse 51 KB, normal 185 KB, ARM 103 KB).
- **Processing applied:** welded, then `gltf-transform simplify --ratio 0.02
  --error 0.02` (5,072 → **354 triangles**), textures resized to 512px,
  dedup, prune. Final file 130 KB. The next decimation step down (error
  0.05, 194 tris) dissolved the chair legs entirely — verified by rendering
  both, not by trusting the numbers. 354 × 286 seats ≈ 101k instanced
  triangles, which sits inside the measured headroom.

**This is the first downloaded asset in the project.** Everything before it was
generated at runtime. It is CC0, so the clear-to-deploy position is intact —
but the position is now something that has to be maintained rather than
something that is true by construction.
