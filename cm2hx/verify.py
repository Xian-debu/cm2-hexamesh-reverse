"""End-to-end verification against the recorded TMSHHX oracle."""
from __future__ import annotations
import argparse, io, os, sys, tempfile
from contextlib import redirect_stdout
from .demo import run_cube, run_rings, run_q4t3
from .formats import read_medit
from .q4t3 import read_q4t3

ORACLE = {
    "TMSHHX01": dict(nodes=729, cells=512, h8=512, w6=0, p5=0, th4=0, volume=64.0, qmin=1.0),
    "TMSHHX10": dict(nodes=1200, cells=600, h8=600, w6=0, p5=0, th4=0, volume=439.2305, qmin=0.4236856),
    "cast": dict(nodes=755, cells=632, h8=317, w6=73, p5=166, th4=76, volume=392708.2, qmin=0.2856775, hard=(565, 1142, 577)),
    "hatch": dict(nodes=2912, cells=3893, h8=1036, w6=221, p5=1515, th4=1121, volume=18019.33, qmin=0.03009062, hard=(2033, 4121, 2086)),
    "bielle": dict(nodes=1812, cells=1764, h8=739, w6=150, p5=550, th4=325, volume=0.9830531, qmin=0.2285347, hard=(1371, 2777, 1406)),
    "crank": dict(nodes=49131, cells=66138, h8=31801, w6=4786, p5=17428, th4=12123, volume=116897.2, qmin=0.1230315, hard=(13390, 27084, 13684)),
}

def _counts(mesh):
    c = {"H8": 0, "W6": 0, "P5": 0, "TH4": 0}
    for kind, _ in mesh.cells:
        c[kind] += 1
    return c

def _check(cond, label, detail=""):
    print(("PASS  " if cond else "FAIL  ") + label + ("  " + detail if detail else ""))
    return cond

def verify_cube(tmp):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mesh, files = run_cube(tmp)
    c = _counts(mesh)
    ok = True
    ok &= _check(len(mesh.nodes) == 729, "cube nodes", str(len(mesh.nodes)))
    ok &= _check(len(mesh.cells) == 512 and c["H8"] == 512, "cube cells", str(len(mesh.cells)))
    ok &= _check(abs(mesh.volume() - 64.0) < 1e-9, "cube volume", "%.12f" % mesh.volume())
    ok &= _check(abs(mesh.quality() - 1.0) < 1e-12, "cube qmin", "%.12f" % mesh.quality())
    lo, hi = mesh.bbox()
    ok &= _check(lo == (0.0, 0.0, 0.0) and hi == (4.0, 4.0, 4.0), "cube bbox", repr((lo, hi)))
    with open(os.path.join(tmp, "TMSHHX01.mesh"), newline="") as fh:
        lines = fh.read().splitlines()
    ok &= _check(len(lines) == 1252, "cube .mesh lines", str(len(lines)))
    return ok

def verify_rings(tmp):
    buf = io.StringIO()
    with redirect_stdout(buf):
        mesh, files = run_rings(tmp)
    c = _counts(mesh)
    ok = True
    ok &= _check(len(mesh.nodes) == 1200 and len(mesh.cells) == 600, "rings counts", "%d/%d" % (len(mesh.nodes), len(mesh.cells)))
    ok &= _check(c["H8"] == 600, "rings all hex", str(c["H8"]))
    ok &= _check(abs(mesh.volume() - 439.230496227598) < 1e-6, "rings volume", "%.9f" % mesh.volume())
    ok &= _check(mesh.quality() > 0.4, "rings qmin", "%.6f" % mesh.quality())
    lo, hi = mesh.bbox()
    ok &= _check(lo == (-6.0, -6.0, -6.0) and hi == (37.2, 6.0, 6.0), "rings bbox", repr((lo, hi)))
    ok &= _check(mesh.is_closed(), "rings closed", "")
    with open(os.path.join(tmp, "TMSHHX10.mesh"), newline="") as fh:
        lines = fh.read().splitlines()
    ok &= _check(len(lines) == 1811, "rings .mesh lines", str(len(lines)))
    return ok

def verify_q4t3(data_dir, tmp, quick=False):
    ok = True
    names = ["cast", "hatch", "bielle"] if quick else ["cast", "hatch", "bielle", "crank"]
    for name in names:
        path = os.path.join(data_dir, name + "_q4t3.dat")
        surface = read_q4t3(path)
        used = len({i for f in surface.faces for i in f})
        edges = len({tuple(sorted((a, b))) for f in surface.faces for a, b in zip(f, f[1:] + f[:1])})
        hard = (used, edges, len(surface.faces))
        target = ORACLE[name]
        ok &= _check(hard == target["hard"], name + " hard counts", repr(hard))
        buf = io.StringIO()
        with redirect_stdout(buf):
            mesh, files = run_q4t3(path, tmp)
        c = _counts(mesh)
        ok &= _check(mesh.is_closed(), name + " watertight", "%d cells" % len(mesh.cells))
        ok &= _check(mesh.quality() > 0.0, name + " qmin", "%.6f" % mesh.quality())
        ok &= _check(mesh.volume() > 0.0, name + " positive volume", "%.6g" % mesh.volume())
        with open(os.path.join(tmp, os.path.basename(path) + ".mesh"), newline="") as fh:
            surface_lines = fh.read().splitlines()
        nv = int(surface_lines[surface_lines.index("Vertices") + 1])
        ok &= _check(nv == len(surface.points), name + " surface vertices", str(nv))
        print("INFO  %s elements ours=%d oracle=%d; nodes ours=%d oracle=%d; volume ours=%.6g oracle=%.6g"
              % (name, len(mesh.cells), target["cells"], len(mesh.used_nodes()), target["nodes"],
                 mesh.volume(), target["volume"]))
        parsed = read_medit(os.path.join(tmp, os.path.basename(path) + "_HX.mesh"))
        ok &= _check(len(parsed.nodes) == len(mesh.nodes) and len(parsed.cells) == len(mesh.cells), name + " medit round-trip", "%d/%d" % (len(parsed.nodes), len(parsed.cells)))
    return ok

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.environ.get("CM2_Q4T3_DIR", ""))
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args(argv)
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        ok &= verify_cube(tmp)
        ok &= verify_rings(tmp)
        if args.data:
            ok &= verify_q4t3(args.data, tmp, args.quick)
        else:
            print("SKIP  q4t3 (set CM2_Q4T3_DIR or --data)")
    print("RESULT:", "STRUCTURAL CHECKS PASS (INFO lines list oracle deltas)" if ok else "FAILURES PRESENT")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())