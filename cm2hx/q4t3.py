"""Reader/writer for the CM2 q4t3 surface format."""
from __future__ import annotations

from dataclasses import dataclass
from .mesh import Mesh


@dataclass
class Surface:
    points: list[tuple[float, float, float]]
    faces: list[tuple[int, ...]]  # 3 or 4 point indices, 0-based

    def to_mesh(self):
        m = Mesh(list(self.points), [])
        return m


def _clean(tokens):
    return [t for t in tokens if t not in ("[", "]", "")]


def read_q4t3(path):
    points = []
    faces = []
    with open(path, "r", encoding="latin-1", newline="") as fh:
        lines = fh.readlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    n = int(_clean(lines[i].split())[0])
    i += 1
    for _ in range(n):
        toks = _clean(lines[i].split())
        points.append((float(toks[0]), float(toks[1]), float(toks[2])))
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    m = int(_clean(lines[i].split())[0])
    i += 1
    for _ in range(m):
        toks = _clean(lines[i].split())
        ids = [int(t) - 1 for t in toks[:4]]
        if ids[3] == 4294967294:  # 0xFFFFFFFF after the 1-based subtraction
            faces.append(tuple(ids[:3]))
        else:
            faces.append(tuple(ids))
        i += 1
    return Surface(points, faces)


def orient_surface(surface):
    """Return a copy of the surface with consistently outward-oriented faces.

    The q4t3 files do not guarantee a global winding.  Two adjacent faces must
    traverse their shared edge in opposite directions; a BFS flip makes that
    true for every connected component.  The global sign is then chosen so the
    enclosed signed volume is positive.
    """
    faces = [tuple(f) for f in surface.faces]
    edge_faces = {}
    for fi, f in enumerate(faces):
        for a, b in zip(f, f[1:] + f[:1]):
            edge_faces.setdefault((a, b) if a < b else (b, a), []).append(fi)
    seen = [False] * len(faces)
    flipped = [False] * len(faces)
    for start in range(len(faces)):
        if seen[start]:
            continue
        seen[start] = True
        queue = [start]
        while queue:
            fi = queue.pop()
            f = faces[fi]
            for a, b in zip(f, f[1:] + f[:1]):
                key = (a, b) if a < b else (b, a)
                for fj in edge_faces[key]:
                    if fj == fi or seen[fj]:
                        continue
                    g = faces[fj]
                    gdir = None
                    for c, d in zip(g, g[1:] + g[:1]):
                        if {c, d} == {a, b}:
                            gdir = (c, d)
                            break
                    if gdir is None:
                        continue
                    same = (gdir == (a, b))
                    flipped[fj] = flipped[fi] ^ same
                    seen[fj] = True
                    queue.append(fj)
    out = []
    for f, flip in zip(faces, flipped):
        out.append(tuple(reversed(f)) if flip else f)
    oriented = Surface(surface.points, out)
    if signed_volume(oriented) < 0:
        oriented = Surface(surface.points, [tuple(reversed(f)) for f in out])
    return oriented


def signed_volume(surface):
    vol = 0.0
    pts = surface.points
    for f in surface.faces:
        p0 = pts[f[0]]
        for k in range(1, len(f) - 1):
            p1, p2 = pts[f[k]], pts[f[k + 1]]
            vol += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
                    - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0])
                    + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])) / 6.0
    return vol


def write_q4t3(path, surface):
    with open(path, "w", encoding="latin-1", newline="") as fh:
        fh.write(f"{len(surface.points)} x 3[\r\n")
        for p in surface.points:
            fh.write("%25.16e %25.16e %25.16e \r\n" % p)
        fh.write(f"{len(surface.faces)} x 4[\r\n")
        for f in surface.faces:
            if len(f) == 3:
                fh.write("%d %d %d 4294967295 \r\n" % tuple(i + 1 for i in f))
            else:
                fh.write("%d %d %d %d \r\n" % tuple(i + 1 for i in f))