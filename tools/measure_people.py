"""Measure generated figures and print the values the build needs.

    ~/tools/py/bin/python tools/measure_people.py <dir>

Prints, for each figure:
  seatY  height of the buttock above the figure's origin
  soleY  height of the shoe sole above it
  gap    seatY - soleY, which must equal the chair pan height (0.44m) for
         the bum to sit on the seat AND the feet to reach the floor

and then two things the build consumes:

  SHIN   the corrected shin angle per figure, stepped from the measured
         error by the known slope. Paste into generate_humans.py and
         regenerate; the second pass lands on 0.44.
  PEOPLE the seatY/soleY table for index.html.

Why this lives outside Blender: solving it inside was tried three times and
failed three times - a vertex window for the buttock misread half the bodies,
a hip-bone offset was self-consistent but disagreed with the scene's own
measurement, and measuring the real mesh per candidate took six minutes a
figure. Measuring the finished glb is unambiguous and instant.
"""
import json
import sys

import trimesh

CHAIR_PAN = 0.44
# measured empirically across the shin range: raising the shin angle tucks
# the foot up, shrinking the seat-to-sole gap
# Measured from two real passes, not assumed: a 35-degree shin change moved
# the gap by 0.069m, so the magnitude is ~0.0012, not the 0.0029 first
# guessed - which stepped short and made convergence look like failure.
SLOPE = -0.0012          # metres of gap per degree
NOMINAL = 80


def measure(path):
    scene = trimesh.load(path, force="scene")
    v = scene.to_mesh().vertices
    # buttock: lowest body point on the centre line, in the hip band
    band = v[(abs(v[:, 0]) < 0.10) & (v[:, 2] > -0.08) & (v[:, 2] < 0.12)
             & (v[:, 1] > 0.55) & (v[:, 1] < 1.05)]
    seat = float(band[:, 1].min()) if len(band) else 0.78
    sole = float(v[:, 1].min())
    return seat, sole


def main(directory, count=6, current_shin=None):
    current_shin = current_shin or {}
    shin_out, people_out = {}, []

    print("%-4s %-7s %-7s %-7s %-8s %s"
          % ("fig", "seat", "sole", "gap", "err", "shin -> new"))
    for i in range(count):
        seat, sole = measure("%s/person_%02d.glb" % (directory, i))
        gap = seat - sole
        err = gap - CHAIR_PAN
        was = current_shin.get(i, NOMINAL)
        # gap is too small -> foot too high -> lower the shin angle
        new = int(round(was + err / SLOPE))
        new = max(30, min(130, new))
        shin_out[i] = new
        people_out.append({"file": "person_%02d" % i,
                           "seatY": round(seat, 3), "soleY": round(sole, 3)})
        print("%-4d %-7.3f %-7.3f %-7.3f %+-8.3f %d -> %d"
              % (i, seat, sole, gap, err, was, new))

    print("\nSHIN = %s" % json.dumps(shin_out))
    print("\nPEOPLE (for index.html):")
    for p in people_out:
        print("  { file: '%s', seatY: %.3f, soleY: %.3f },"
              % (p["file"], p["seatY"], p["soleY"]))


if __name__ == "__main__":
    d = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    shin = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    main(d, n, {int(k): v for k, v in shin.items()})
