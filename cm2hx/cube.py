"""Exact structured grid used by the TMSHHX01 - CUBE case."""
from __future__ import annotations

from .mesh import Mesh


def cube(n=8):
    """A Cartesian n^3 hex grid over [0, n/2]^3; geometry matches the oracle."""
    if n < 1:
        raise ValueError("n must be positive")
    m = n + 1
    step = 0.5
    mesh = Mesh()
    index = {}
    for k in range(m):
        for j in range(m):
            for i in range(m):
                index[(i, j, k)] = mesh.add_node((i * step, j * step, k * step))
    for k in range(n):
        for j in range(n):
            for i in range(n):
                v = (index[(i, j, k)], index[(i + 1, j, k)], index[(i + 1, j + 1, k)],
                     index[(i, j + 1, k)], index[(i, j, k + 1)], index[(i + 1, j, k + 1)],
                     index[(i + 1, j + 1, k + 1)], index[(i, j + 1, k + 1)])
                mesh.add_cell("H8", v)
    return mesh
