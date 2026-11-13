"""Structured chain of five convex-octagon rings (TMSHHX10)."""
from __future__ import annotations

import math

from .mesh import Mesh

# Convex-octagon profile in (radius, z), centred at r=5; area 2+sqrt(2).
PROFILE = [
    (6.0, 0.0), (5.7071068, 0.7071068), (5.0, 1.0), (4.2928932, 0.7071068),
    (4.0, 0.0), (4.2928932, -0.7071068), (5.0, -1.0), (5.7071068, -0.7071068),
]


def _rot_x(p, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return (p[0], c * p[1] - s * p[2], s * p[1] + c * p[2])


def rings(stations=24, count=5, spacing=7.8, max_half_height=1.0,
          interior=((5.05, 0.15), (4.75, -0.15))):
    """Five interlocking rings, 25 hexes per angular station (600 cells)."""
    mesh = Mesh()
    for ring in range(count):
        # One row of nine cross-section nodes per angular station:
        # eight diamond-boundary nodes plus the centre, ordered around the profile.
        rows = []
        for s in range(stations):
            ang = 2.0 * math.pi * s / stations
            ca, sa = math.cos(ang), math.sin(ang)
            row = []
            for rr, zz in PROFILE:
                p = (rr * ca, rr * sa, zz * max_half_height)
                p = _rot_x(p, 90.0 * ring)
                row.append(mesh.add_node((p[0] + spacing * ring, p[1], p[2])))
            p = (5.0 * ca, 5.0 * sa, 0.0)
            p = _rot_x(p, 90.0 * ring)
            # Two interior nodes complete a five-quad cross-section (10 nodes/station).
            for qq in interior:
                p2 = (qq[0] * ca, qq[0] * sa, qq[1])
                p2 = _rot_x(p2, 90.0 * ring)
                row.append(mesh.add_node((p2[0] + spacing * ring, p2[1], p2[2])))
            rows.append(row)
        # Four quads per station (each spans two profile edges); sweep them.
        quads = [
            (8, 2, 1, 0), (8, 9, 3, 2), (9, 5, 4, 3),
            (9, 7, 6, 5), (8, 0, 7, 9),
        ]
        for s in range(stations):
            cur = rows[s]
            nxt = rows[(s + 1) % stations]
            for q in quads:
                v = tuple(cur[i] for i in q) + tuple(nxt[i] for i in q)
                mesh.add_cell("H8", v)
    return mesh