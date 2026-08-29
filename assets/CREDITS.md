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

---

## `people/person_0*.glb` — the front-row audience

- **What it is:** six clothed, seated human figures for the front rows,
  **generated on this machine** rather than downloaded, by MPFB2 (MakeHuman
  for Blender) driven headless from `tools/generate_humans.py`. Each is a
  different body — gender, age, build, height, ethnicity are numeric inputs.
- **Author / vendor:** derived from the MakeHuman base mesh (Data Collection
  AB, Joel Palmius, Jonas Hauquier) plus the MakeHuman system assets pack
  (clothes, hair, shoes) by the MakeHuman community.
- **Licence:** **CC0, established at the source, not by hearsay.** The base
  mesh states it in its own file header: *"This asset was explicitly released
  as CC0 in september 2020"*, with the copyright holders named — see
  `data/3dobjs/base.obj` inside the MPFB package. The clothes and hair come
  from `makehuman_system_assets_cc0.zip`, every asset listed CC0 on
  <https://static.makehumancommunity.org/assets/assetpacks/makehuman_system_assets.html>.
  MPFB itself is GPL-3.0-or-later, which covers the **tool**, not its output.
- **Source form:** MPFB base mesh (~18.5k polys) + fitted mhclo garments.
- **Processing applied:** rig, seated pose applied as the **rest** pose with
  the armature kept live, garments fitted afterwards, textures to 256px,
  prune. Nothing is decimated. 1.1–1.5 MB per figure, 7.4 MB for the set of
  six.
- **The arm pose is solved, not guessed** - `tools/solve_arm_pose.py`. Six
  hand-picked attempts all failed (palms up as if meditating, hands dangling
  beside the seat, forearms held out like a steering wheel), because this
  rig's axes do not match any intuition: increasing the ELBOW angle RAISES
  the hand, and palm orientation is set by the UPPER ARM's roll, not the
  wrist. The solver grid-searches the angles and scores each by how close the
  wrist lands to a target measured on the figure's own thigh.

  The clearance above that target matters as much as the angles. It was set
  0.085 above the thigh BONE, and the bone runs down the middle of the leg —
  so the solver dutifully placed the wrist *inside* the thigh. The palm sank
  into the flesh with only fingertips emerging, which reads as a mangled hand
  at any distance. Clearance is now 0.155: thigh radius plus half a hand.
- **Why the skeleton ships:** an earlier version baked the pose flat and cut
  the head off as a separate object so it could be rotated. That left an open
  hole at the neck - visible as white shrapnel - and swung a rigid skull off
  the shoulders whenever it turned. Keeping the armature lets the mesh deform
  continuously instead.
- **Nothing is decimated.** Garments are fitted meshes, tied vertex by vertex
  to the body beneath, so collapsing either one alone pulls the two surfaces
  apart and the body erupts through the shirt. Triangles were never the
  constraint here.
- **Garments are not rigged; hair is.** Skinning a fitted garment to the
  body's skeleton tore every shirt apart: interpolated weights give chest
  vertices near the armpit a share of the ARM bones, so the seated shoulder
  rotation drags them out into shards. Proved by elimination — an unposed,
  unrigged fit is flawless, subdivision made no difference, fitting order
  made no difference, removing the rigging fixed it outright. Nothing about
  a shirt moves at runtime; only the neck rotates, which is why hair keeps
  its rigging.
- **Clothes are fitted AFTER the pose is baked**, since they carry no
  skinning to deform them into it. The helper masks must not be applied
  before that: mhclo maps garments onto the full base mesh *including* the
  helper vertices, so deleting them first makes the import index past the
  end of the mesh and fail.

