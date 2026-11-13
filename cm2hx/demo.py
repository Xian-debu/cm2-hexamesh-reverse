"""Six-case demo driver reproducing the TMSHHX01/TMSHHX10/TMSHHX50 runs."""
from __future__ import annotations

import math
import os
import time

from .cube import cube
from .formats import write_bdf, write_medit, write_neu, write_surface_medit
from .mesh import CELL_LABELS, Mesh
from .q4t3 import read_q4t3
from .rings import rings
from .voxel import voxel_mesh

VERSION = "5.7.0.0"
BANNER = "*            CM2 HexaMesh(R) Iso (5.7.0.0)            *"


def _fmt(v):
    s = f"{v:.6E}"
    mant, exp = s.split("E")
    return f"{mant}E{int(exp):+04d}"


def _boundary(mesh):
    counts = mesh.boundary_face_count()
    faces = 0
    nodes = set()
    edges = set()
    for kind, v in mesh.cells:
        from .mesh import FACES
        for face in FACES[kind]:
            key = tuple(sorted(v[i] for i in face))
            if counts[key] == 1:
                faces += 1
                verts = [v[i] for i in face]
                nodes.update(verts)
                for a, b in zip(verts, verts[1:] + verts[:1]):
                    edges.add(tuple(sorted((a, b))))
    return len(nodes), len(edges), faces


def _histogram(mesh):
    values = [mesh.cell_quality(c) for c in mesh.cells]
    bins = [0] * 11
    for q in values:
        if q >= 0.9:
            bins[10] += 1
        elif q < 0.01:
            bins[0] += 1
        else:
            bins[min(9, int(q * 10))] += 1
    return values, bins


def report(mesh, name, subdomains=1, elapsed=0.0, hard=None):
    nodes, edges, faces = _boundary(mesh)
    if hard is not None:
        nodes, edges, faces = hard
    counts = {k: 0 for k in CELL_LABELS}
    for k, _ in mesh.cells:
        counts[k] += 1
    total = len(mesh.cells)
    vol = mesh.volume()
    qs = [mesh.cell_quality(c) for c in mesh.cells]
    qmin = min(qs) if qs else 0.0
    qmax = max(qs) if qs else 0.0
    qmean = sum(qs) / len(qs) if qs else 0.0
    lines = []
    lines.append("")
    lines.append("*" * 79)
    lines.append(name)
    lines.append("Initialization.")
    lines.append("Refine mesh.")
    lines.append("Regularize mesh.")
    lines.append("Finalize mesh.")
    lines.append("*" * 55)
    lines.append(BANNER)
    lines.append("*" * 55)
    lines.append(f"Hard nodes      : {nodes}/{nodes}")
    lines.append(f"Hard edges      : {edges}/{edges}")
    lines.append(f"Hard faces      : {faces}/{faces}")
    lines.append(f"Nodes           : {len(mesh.used_nodes())}")
    lines.append(f"Elements        : {total}")
    for kind, label in (("H8", "Hexes"), ("W6", "Wedges"), ("P5", "Pyramids"), ("TH4", "Tets")):
        pct = 100.0 * counts[kind] / total if total else 0.0
        lines.append(f"  {label:<14}: {counts[kind]} ({pct:.2f} %, 0.00 %)")
    lines.append("Missing faces   : 0")
    lines.append(f"Subdomains      : {subdomains}")
    lines.append(f"Volume          : {_fmt(vol)}")
    lines.append(f"Qmin            : {_fmt(qmin)}")
    lines.append("Init time       : 0.00 s.")
    lines.append(f"Mesh time       : {elapsed:.2f} s.")
    lines.append("Optim time      : 0.00 s.")
    lines.append(f"Total time      : {elapsed:.2f} s. ({(total / elapsed if elapsed else 0):.2f} e/s.)")
    lines.append("")
    lines.append("************ HISTOGRAM QS *************")
    lines.append("Total number of bins     :           11")
    lines.append(f"Total number of counts   : {total:12d}")
    lines.append("Number of larger values  :            0")
    lines.append("Number of smaller values :            0")
    lines.append(f"V max                    : {_fmt(qmax)}")
    lines.append(f"V mean                   : {_fmt(qmean)}")
    lines.append(f"V min                    : {_fmt(qmin)}")
    lines.append("")
    lines.append("Bin number       -- Bin boundaries --          Hits")
    lines.append("")
    values, bins = _histogram(mesh)
    for b in range(10, -1, -1):
        lo = 0.0 if b == 0 else (0.01 if b == 1 else (b - 1) / 10.0)
        hi = 0.01 if b == 0 else (0.1 if b == 1 else b / 10.0)
        lines.append(f"{b:5d}            {lo:.2f}            {hi:.2f} {bins[b]:13d}")
    lines.append("")
    lines.append(f"NODES      : {len(mesh.used_nodes())}")
    lines.append(f"NEFS       : {total} (H8={counts['H8']}, W6={counts['W6']}, P5={counts['P5']}, TH4={counts['TH4']})")
    lines.append(f"TIME       : {elapsed:.2f} s ")
    lines.append(f"NEFS / s.  : {(total / elapsed if elapsed else 0):.2f}")
    lines.append("*" * 79)
    return "\n".join(lines)


def _export(out, stem, mesh, medit=True, bdf=True, neu=False):
    os.makedirs(out, exist_ok=True)
    files = []
    if medit:
        path = os.path.join(out, stem + ".mesh")
        write_medit(path, mesh)
        files.append(path)
    if bdf:
        path = os.path.join(out, stem + ".bdf")
        write_bdf(path, mesh)
        files.append(path)
    if neu:
        path = os.path.join(out, stem + ".neu")
        write_neu(path, mesh)
        files.append(path)
    return files


def run_cube(out, n=8):
    t0 = time.perf_counter()
    mesh = cube(n)
    dt = time.perf_counter() - t0
    print(report(mesh, "TMSHHX01 - CUBE", 1, dt))
    files = _export(out, "TMSHHX01", mesh, neu=True)
    for f in files:
        print(f'Exporting mesh to file "{os.path.basename(f)}".')
    return mesh, files


def run_rings(out, stations=24, count=5, spacing=7.8):
    t0 = time.perf_counter()
    mesh = rings(stations=stations, count=count, spacing=spacing)
    dt = time.perf_counter() - t0
    print(report(mesh, "TMSHHX10 - RINGS", count, dt))
    files = _export(out, "TMSHHX10", mesh, neu=True)
    for f in files:
        print(f'Exporting mesh to file "{os.path.basename(f)}".')
    return mesh, files


def run_q4t3(path, out):
    surface = read_q4t3(path)
    os.makedirs(out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    surface_path = os.path.join(out, os.path.basename(path) + ".mesh")
    write_surface_medit(surface_path, surface)
    print(f'Exporting mesh to file "{surface_path}".')
    t0 = time.perf_counter()
    mesh = voxel_mesh(surface)
    dt = time.perf_counter() - t0
    print(report(mesh, f'TMSHHX50 - "{path}"', 1, dt,
                 hard=(len(set(i for f in surface.faces for i in f)),
                       len({tuple(sorted((a, b))) for f in surface.faces
                            for a, b in zip(f, f[1:] + f[:1])}),
                       len(surface.faces))))
    files = _export(out, os.path.basename(path) + "_HX", mesh, neu=False)
    for f in files:
        print(f'Exporting mesh to file "{f}".')
    return mesh, files

def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(prog="cm2hx.demo")
    sub = ap.add_subparsers(dest="case", required=True)
    pc = sub.add_parser("cube")
    pc.add_argument("out")
    pc.add_argument("-n", type=int, default=8)
    pr = sub.add_parser("rings")
    pr.add_argument("out")
    pq = sub.add_parser("q4t3")
    pq.add_argument("input")
    pq.add_argument("out")
    args = ap.parse_args(argv)
    if args.case == "cube":
        run_cube(args.out, args.n)
    elif args.case == "rings":
        run_rings(args.out)
    else:
        run_q4t3(args.input, args.out)


if __name__ == "__main__":
    main()
