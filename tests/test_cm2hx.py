import math
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cm2hx.cube import cube
from cm2hx.formats import read_medit, write_medit, write_bdf, write_neu
from cm2hx.mesh import Mesh
from cm2hx.q4t3 import read_q4t3, write_q4t3
from cm2hx.rings import rings


class CubeTest(unittest.TestCase):
    def test_counts_and_volume(self):
        m = cube(8)
        self.assertEqual(len(m.nodes), 729)
        self.assertEqual(len(m.cells), 512)
        self.assertAlmostEqual(m.volume(), 64.0, places=12)
        self.assertAlmostEqual(m.quality(), 1.0, places=12)
        self.assertEqual(m.bbox(), ((0.0, 0.0, 0.0), (4.0, 4.0, 4.0)))

    def test_medit_roundtrip(self):
        m = cube(4)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.mesh")
            write_medit(path, m)
            r = read_medit(path)
        self.assertEqual(len(r.nodes), len(m.nodes))
        self.assertEqual(len(r.cells), len(m.cells))
        self.assertAlmostEqual(r.volume(), m.volume(), places=9)


class RingsTest(unittest.TestCase):
    def test_counts_volume_bbox(self):
        m = rings()
        self.assertEqual(len(m.nodes), 1200)
        self.assertEqual(len(m.cells), 600)
        self.assertAlmostEqual(m.volume(), 439.230496227598, places=6)
        self.assertGreater(m.quality(), 0.4)
        self.assertEqual(m.bbox(), ((-6.0, -6.0, -6.0), (37.2, 6.0, 6.0)))

    def test_closed_surface(self):
        m = rings()
        self.assertTrue(m.is_closed())


class Q4T3Test(unittest.TestCase):
    DATA = os.environ.get("CM2_Q4T3_DIR", os.path.join(ROOT, "data"))

    def test_surface_closure(self):
        path = os.path.join(self.DATA, "cast_q4t3.dat")
        if not os.path.exists(path):
            self.skipTest("cast_q4t3.dat not present")
        s = read_q4t3(path)
        self.assertEqual(len(s.points), 619)
        self.assertEqual(len(s.faces), 577)
        edges = {}
        for f in s.faces:
            for a, b in zip(f, f[1:] + f[:1]):
                key = tuple(sorted((a, b)))
                edges[key] = edges.get(key, 0) + 1
        self.assertEqual(len(edges), 1142)
        self.assertEqual(set(edges.values()), {2})

    def test_roundtrip(self):
        path = os.path.join(self.DATA, "cast_q4t3.dat")
        if not os.path.exists(path):
            self.skipTest("cast_q4t3.dat not present")
        s = read_q4t3(path)
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "s.dat")
            write_q4t3(out, s)
            t = read_q4t3(out)
        self.assertEqual(s.points, t.points)
        self.assertEqual(s.faces, t.faces)


class FormatTest(unittest.TestCase):
    def test_cube_line_counts(self):
        m = cube(8)
        with tempfile.TemporaryDirectory() as tmp:
            paths = [os.path.join(tmp, n) for n in ("a.mesh", "a.bdf", "a.neu")]
            write_medit(paths[0], m)
            write_bdf(paths[1], m)
            write_neu(paths[2], m)
            counts = []
            for p in paths:
                with open(p, newline="") as fh:
                    counts.append(len(fh.read().splitlines()))
        self.assertEqual(counts, [1252, 2496, 4325])

    def test_medit_omits_wedges(self):
        m = Mesh()
        for p in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (0, 1, 1)):
            m.add_node(p)
        m.add_cell("W6", (0, 1, 2, 3, 4, 5))
        with tempfile.TemporaryDirectory() as tmp:
            mesh_path = os.path.join(tmp, "w.mesh")
            bdf_path = os.path.join(tmp, "w.bdf")
            write_medit(mesh_path, m)
            write_bdf(bdf_path, m)
            with open(mesh_path, encoding="latin-1") as fh:
                mesh_text = fh.read()
            with open(bdf_path, encoding="latin-1") as fh:
                bdf_text = fh.read()
        self.assertNotIn("Prisms", mesh_text)
        self.assertNotIn("Wedges", mesh_text)
        self.assertIn("CPENTA", bdf_text)

    def test_crlf_line_endings(self):
        m = cube(2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.mesh")
            write_medit(path, m)
            with open(path, "rb") as fh:
                raw = fh.read()
        self.assertNotIn(b"\r\r\n", raw)
        self.assertTrue(raw.endswith(b"\r\n"))


if __name__ == "__main__":
    unittest.main()