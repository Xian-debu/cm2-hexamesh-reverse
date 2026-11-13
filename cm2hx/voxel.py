"""Voxel/occupancy hex mesher for arbitrary closed q4t3 surfaces.

The implementation deliberately favours a valid, watertight hex mesh over a
byte-identical reproduction of the vendor's octree boundary templates.
"""
from __future__ import annotations

import math
from collections import deque

from .mesh import Mesh


def triangles(surface):
    tris = []
    for f in surface.faces:
        if len(f) == 3:
            tris.append(tuple(f))
        else:
            a, b, c, d = f
            tris.append((a, b, c))
            tris.append((a, c, d))
    return tris


def edge_percentile(surface, q=0.25):
    vals = []
    for f in surface.faces:
        for a, b in zip(f, f[1:] + f[:1]):
            pa, pb = surface.points[a], surface.points[b]
            vals.append(math.dist(pa, pb))
    vals.sort()
    if not vals:
        return 1.0
    return vals[min(len(vals) - 1, int(q * len(vals)))]


def surface_volume(surface):
    vol = 0.0
    for a, b, c in triangles(surface):
        p0, p1, p2 = surface.points[a], surface.points[b], surface.points[c]
        vol += (p0[0] * (p1[1] * p2[2] - p1[2] * p2[1])
                - p0[1] * (p1[0] * p2[2] - p1[2] * p2[0])
                + p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])) / 6.0
    return abs(vol)


def _tri_bbox(tri, pts):
    return (min(pts[i][0] for i in tri), max(pts[i][0] for i in tri),
            min(pts[i][1] for i in tri), max(pts[i][1] for i in tri),
            min(pts[i][2] for i in tri), max(pts[i][2] for i in tri))


def _point_tri_dist2(p, a, b, c):
    # Ericson, Real-Time Collision Detection, squared distance.
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    ap = (p[0] - a[0], p[1] - a[1], p[2] - a[2])
    d1 = ab[0] * ap[0] + ab[1] * ap[1] + ab[2] * ap[2]
    d2 = ac[0] * ap[0] + ac[1] * ap[1] + ac[2] * ap[2]
    if d1 <= 0 and d2 <= 0:
        return ap[0] ** 2 + ap[1] ** 2 + ap[2] ** 2
    bp = (p[0] - b[0], p[1] - b[1], p[2] - b[2])
    d3 = ab[0] * bp[0] + ab[1] * bp[1] + ab[2] * bp[2]
    d4 = ac[0] * bp[0] + ac[1] * bp[1] + ac[2] * bp[2]
    if d3 >= 0 and d4 <= d3:
        return bp[0] ** 2 + bp[1] ** 2 + bp[2] ** 2
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        t = d1 / (d1 - d3)
        q = (a[0] + t * ab[0], a[1] + t * ab[1], a[2] + t * ab[2])
        return sum((p[i] - q[i]) ** 2 for i in range(3))
    cp = (p[0] - c[0], p[1] - c[1], p[2] - c[2])
    d5 = ab[0] * cp[0] + ab[1] * cp[1] + ab[2] * cp[2]
    d6 = ac[0] * cp[0] + ac[1] * cp[1] + ac[2] * cp[2]
    if d6 >= 0 and d5 <= d6:
        return cp[0] ** 2 + cp[1] ** 2 + cp[2] ** 2
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        t = d2 / (d2 - d6)
        q = (a[0] + t * ac[0], a[1] + t * ac[1], a[2] + t * ac[2])
        return sum((p[i] - q[i]) ** 2 for i in range(3))
    va = d3 * d6 - d5 * d4
    if va <= 0 and (d4 - d3) >= 0 and (d5 - d6) >= 0:
        t = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        q = (b[0] + t * (c[0] - b[0]), b[1] + t * (c[1] - b[1]), b[2] + t * (c[2] - b[2]))
        return sum((p[i] - q[i]) ** 2 for i in range(3))
    den = 1.0 / (va + vb + vc)
    v = vb * den
    w = vc * den
    q = (a[0] + ab[0] * v + ac[0] * w, a[1] + ab[1] * v + ac[1] * w, a[2] + ab[2] * v + ac[2] * w)
    return sum((p[i] - q[i]) ** 2 for i in range(3))


def _triangles_bilinear(surface):
    """Triangulate quads along the b-c diagonal (the warped-patch convention)."""
    tris = []
    for f in surface.faces:
        if len(f) == 3:
            tris.append(tuple(f))
        else:
            a, b, c, d = f
            tris.append((a, b, d))
            tris.append((b, c, d))
    return tris


def _column_crossings(x, y, tris, pts, eps):
    """Z values where the vertical line (x+eps, y+eps) crosses the surface."""
    out = []
    for tri in tris:
        a, b, c = pts[tri[0]], pts[tri[1]], pts[tri[2]]
        x0, y0 = a[0], a[1]
        x1, y1 = b[0], b[1]
        x2, y2 = c[0], c[1]
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-12:
            continue
        l1 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / det
        l2 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / det
        l3 = 1.0 - l1 - l2
        if l1 < -eps or l2 < -eps or l3 < -eps:
            continue
        out.append(l1 * a[2] + l2 * b[2] + l3 * c[2])
    out.sort()
    return out


def voxel_mesh(surface, h=None, scale=0.85):
    """Fill the closed surface with axis-aligned hexahedra.

    A vertical ray per grid column is intersected with the triangulated
    surface; parity of the crossings decides which cells are inside.  The
    result is watertight and topologically valid, but its stair-stepped
    boundary does not reproduce the vendor's surface-fitted templates.
    """
    pts = surface.points
    tris = _triangles_bilinear(surface)
    if h is None:
        h = edge_percentile(surface, 0.25) * scale
        if h <= 0:
            h = 1.0
    lo = [min(p[i] for p in pts) - 0.5 * h for i in range(3)]
    hi = [max(p[i] for p in pts) + 0.5 * h for i in range(3)]
    nx = max(1, int(math.ceil((hi[0] - lo[0]) / h)))
    ny = max(1, int(math.ceil((hi[1] - lo[1]) / h)))
    nz = max(1, int(math.ceil((hi[2] - lo[2]) / h)))
    eps = 1e-9

    mesh = Mesh()
    node_map = {}

    def corner(i, j, k):
        key = (i, j, k)
        n = node_map.get(key)
        if n is None:
            n = mesh.add_node((lo[0] + key[0] * h, lo[1] + key[1] * h, lo[2] + key[2] * h))
            node_map[key] = n
        return n

    for i in range(nx):
        x = lo[0] + (i + 0.5) * h
        for j in range(ny):
            y = lo[1] + (j + 0.5) * h
            zs = _column_crossings(x, y, tris, pts, eps)
            if len(zs) < 2:
                continue
            for k in range(nz):
                z = lo[2] + (k + 0.5) * h
                inside = False
                for q in range(0, len(zs) - 1, 2):
                    if zs[q] <= z <= zs[q + 1]:
                        inside = True
                        break
                if not inside:
                    continue
                ids = [corner(i, j, k), corner(i + 1, j, k), corner(i + 1, j + 1, k), corner(i, j + 1, k),
                       corner(i, j, k + 1), corner(i + 1, j, k + 1), corner(i + 1, j + 1, k + 1), corner(i, j + 1, k + 1)]
                mesh.add_cell("H8", ids)
    return mesh
