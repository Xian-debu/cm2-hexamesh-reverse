"""Minimal mesh container and geometric predicates (stdlib only)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CELL_SIZES = {"H8": 8, "W6": 6, "P5": 5, "TH4": 4}
CELL_LABELS = {"H8": "Hexes", "W6": "Wedges", "P5": "Pyramids", "TH4": "Tets"}

# Outward-oriented faces, matching the vertex ordering used by the CM2 writers.
FACES = {
    "H8": [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
    "W6": [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)],
    "P5": [(0, 3, 2, 1), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)],
    "TH4": [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)],
}


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def norm(a):
    return math.sqrt(dot(a, a))


@dataclass
class Mesh:
    nodes: list[tuple[float, float, float]] = field(default_factory=list)
    cells: list[tuple[str, tuple[int, ...]]] = field(default_factory=list)

    def add_node(self, p):
        self.nodes.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.nodes) - 1

    def add_cell(self, kind, verts):
        if kind not in CELL_SIZES or len(verts) != CELL_SIZES[kind]:
            raise ValueError(f"bad cell {kind} {verts}")
        self.cells.append((kind, tuple(int(v) for v in verts)))

    def cell_volume(self, cell):
        kind, v = cell
        pts = [self.nodes[i] for i in v]
        vol = 0.0
        for face in FACES[kind]:
            p0 = pts[face[0]]
            for k in range(1, len(face) - 1):
                p1, p2 = pts[face[k]], pts[face[k + 1]]
                vol += dot(p0, cross(p1, p2)) / 6.0
        return vol

    def volume(self):
        return sum(self.cell_volume(c) for c in self.cells)

    def bbox(self):
        if not self.nodes:
            return ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        lo = tuple(min(p[i] for p in self.nodes) for i in range(3))
        hi = tuple(max(p[i] for p in self.nodes) for i in range(3))
        return (lo, hi)

    def used_nodes(self):
        used = set()
        for _, v in self.cells:
            used.update(v)
        return used

    def compact(self, keep_unused=False):
        used = self.used_nodes()
        if keep_unused or len(used) == len(self.nodes):
            return self
        remap = {}
        nodes = []
        for i, p in enumerate(self.nodes):
            if i in used:
                remap[i] = len(nodes)
                nodes.append(p)
        cells = [(k, tuple(remap[i] for i in v)) for k, v in self.cells]
        return Mesh(nodes, cells)

    def cell_quality(self, cell):
        """Scaled Jacobian of one cell (0..1; larger is better)."""
        kind, v = cell
        pts = [self.nodes[i] for i in v]
        if kind == "H8":
            best = 1.0
            nb = {0: (1, 3, 4), 1: (0, 2, 5), 2: (1, 3, 6), 3: (0, 2, 7),
                  4: (0, 5, 7), 5: (1, 4, 6), 6: (2, 5, 7), 7: (3, 4, 6)}
            for i, (a, b, c) in nb.items():
                q = abs(dot(sub(pts[a], pts[i]), cross(sub(pts[b], pts[i]), sub(pts[c], pts[i]))))
                den = norm(sub(pts[a], pts[i])) * norm(sub(pts[b], pts[i])) * norm(sub(pts[c], pts[i]))
                if den > 0:
                    best = min(best, q / den)
            return best
        if kind == "TH4":
            best = 1.0
            for i in range(4):
                js = [j for j in range(4) if j != i]
                a, b, c = (sub(pts[j], pts[i]) for j in js)
                den = norm(a) * norm(b) * norm(c)
                if den > 0:
                    best = min(best, abs(dot(a, cross(b, c))) / den)
            return best
        best = 0.0
        for i in range(len(v)):
            edges = [sub(pts[j], pts[i]) for j in range(len(v)) if j != i]
            val = 0.0
            for a in range(len(edges)):
                for b in range(a + 1, len(edges)):
                    for c in range(b + 1, len(edges)):
                        ea, eb, ec = edges[a], edges[b], edges[c]
                        den = norm(ea) * norm(eb) * norm(ec)
                        if den > 0:
                            val = max(val, abs(dot(ea, cross(eb, ec))) / den)
            best = max(best, val)
        return best

    def quality(self):
        """Minimum scaled Jacobian over all cells (1.0 for an orthogonal cube)."""
        best = 1.0
        for cell in self.cells:
            best = min(best, self.cell_quality(cell))
        return best

    def boundary_face_count(self):
        count = {}
        for kind, v in self.cells:
            for face in FACES[kind]:
                key = tuple(sorted(v[i] for i in face))
                count[key] = count.get(key, 0) + 1
        return count

    def is_closed(self):
        """Manifold and watertight for a volume mesh: every face used once or twice."""
        counts = self.boundary_face_count().values()
        return bool(counts) and all(c in (1, 2) for c in counts)

    def is_surface_closed(self):
        """True for a closed surface: every edge is shared by exactly two faces."""
        return all(c == 2 for c in self.boundary_face_count().values())

    def stats(self):
        total = len(self.cells)
        counts = {k: 0 for k in CELL_SIZES}
        for k, _ in self.cells:
            counts[k] += 1
        return {
            "nodes": len(self.used_nodes()),
            "vertices": len(self.nodes),
            "elements": total,
            "counts": counts,
            "volume": self.volume(),
            "qmin": self.quality(),
            "closed": self.is_closed(),
        }