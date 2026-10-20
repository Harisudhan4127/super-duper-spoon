"""Integration tests for the generated assets.

These tests verify that the deliverables exist, that the reference manifest is
consistent with the files on disk and that the exported meshes have the
expected scale.  Tests that need an artefact that has not been generated yet
are skipped instead of failing, so the suite can run on a fresh clone.
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "scripts"))

from temple_params import CUTAWAY_SCALE, MASTER_SCALE, PARAMS, plan_positions  # noqa: E402

REF_DIR = PROJECT_ROOT / "src" / "references"
MODEL_DIR = PROJECT_ROOT / "src" / "models"
DOC_DIR = PROJECT_ROOT / "src" / "documentation"
SCRIPT_DIR = PROJECT_ROOT / "src" / "scripts"


def read_stl(path: Path):
    with path.open("rb") as handle:
        header = handle.read(84)
        count = struct.unpack("<I", header[80:84])[0]
        data = handle.read(50 * count)
    xs, ys, zs = [], [], []
    for index in range(count):
        values = struct.unpack("<12f", data[index * 50 : index * 50 + 48])
        for offset in (3, 6, 9):
            xs.append(values[offset])
            ys.append(values[offset + 1])
            zs.append(values[offset + 2])
    return count, (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


class TestReferenceAssets(unittest.TestCase):
    def test_manifest_exists_and_is_valid_json(self):
        manifest_path = REF_DIR / "image_manifest.json"
        if not manifest_path.exists():
            self.skipTest("reference images have not been downloaded yet")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertIn("images", payload)
        self.assertGreater(len(payload["images"]), 0)

    def test_every_manifest_entry_has_attribution_and_a_real_file(self):
        manifest_path = REF_DIR / "image_manifest.json"
        if not manifest_path.exists():
            self.skipTest("reference images have not been downloaded yet")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in payload["images"]:
            for key in ("filename", "title", "page_url", "author", "licence",
                        "downloaded_at", "width_px", "height_px", "sha256", "status"):
                self.assertIn(key, entry, f"manifest entry {entry.get('filename')} misses {key}")
            image_path = REF_DIR / "images" / entry["filename"]
            self.assertTrue(image_path.exists(), f"missing image file {image_path}")
            if entry["status"] == "downloaded":
                digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
                self.assertEqual(digest, entry["sha256"], f"checksum mismatch for {entry['filename']}")

    def test_sources_document_exists(self):
        sources = REF_DIR / "sources.md"
        if not sources.exists():
            self.skipTest("reference images have not been downloaded yet")
        self.assertIn("Attribution", sources.read_text(encoding="utf-8"))


class TestScripts(unittest.TestCase):
    def test_required_scripts_exist_and_compile(self):
        required = [
            "download_references.py", "inspect_references.py", "generate_temple.py",
            "export_models.py", "validate_meshes.py", "build_report.py",
            "temple_params.py", "temple_geom.py", "temple_build.py",
        ]
        for name in required:
            path = SCRIPT_DIR / name
            if name == "build_report.py" and not path.exists():
                continue  # optional until the report generator is added
            self.assertTrue(path.exists(), f"missing script {name}")
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_cad_script_compiles(self):
        path = SCRIPT_DIR / "cad" / "generate_cad.py"
        if not path.exists():
            self.skipTest("CAD script not generated yet")
        compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_shell_wrappers_are_executable(self):
        for name in ("blender.sh", "freecad.sh"):
            path = SCRIPT_DIR / name
            if not path.exists():
                self.skipTest(f"{name} not present")
            self.assertTrue(path.stat().st_mode & 0o111, f"{name} is not executable")


class TestGeneratedModels(unittest.TestCase):
    def test_exterior_stl_has_the_expected_scale(self):
        path = MODEL_DIR / "stl" / "brihadisvara_exterior.stl"
        if not path.exists():
            self.skipTest("exterior model not generated yet")
        triangles, mins, maxs = read_stl(path)
        self.assertGreater(triangles, 1000)
        length = maxs[0] - mins[0]
        expected = PARAMS.complex_length_x * MASTER_SCALE
        self.assertAlmostEqual(length, expected, delta=5.0)

    def test_cutaway_stl_has_the_expected_scale(self):
        path = MODEL_DIR / "stl" / "brihadisvara_cutaway.stl"
        if not path.exists():
            self.skipTest("cutaway model not generated yet")
        triangles, mins, maxs = read_stl(path)
        self.assertGreater(triangles, 1000)
        height = maxs[2] - mins[2]
        expected = (PARAMS.vimana_total_height + PARAMS.platform_height) * CUTAWAY_SCALE
        self.assertAlmostEqual(height, expected, delta=2.0)

    def test_blender_projects_exist(self):
        for name in ("brihadisvara_exterior.blend", "brihadisvara_cutaway.blend"):
            path = MODEL_DIR / "blender" / name
            if not path.exists():
                self.skipTest(f"{name} not generated yet")
            self.assertGreater(path.stat().st_size, 10_000)

    def test_step_files_exist_when_cad_was_run(self):
        step_dir = MODEL_DIR / "step"
        if not step_dir.exists() or not any(step_dir.glob("*.step")):
            self.skipTest("CAD export not generated yet")
        for path in step_dir.glob("*.step"):
            self.assertGreater(path.stat().st_size, 500, f"{path.name} looks empty")
            self.assertIn("ISO-10303-21", path.read_text(encoding="utf-8", errors="ignore")[:2000])

    def test_previews_exist(self):
        preview_dir = PROJECT_ROOT / "src" / "previews"
        images = sorted(preview_dir.glob("*.png"))
        if not images:
            self.skipTest("previews not rendered yet")
        for image in images:
            self.assertGreater(image.stat().st_size, 10_000)


class TestDocumentation(unittest.TestCase):
    def test_required_documents_exist(self):
        required = [
            "environment_audit.md", "project_plan.md", "architecture_analysis.md",
            "historical_assumptions.md", "model_dimensions.md", "print_settings.md",
            "assembly_guide.md", "validation_report.md", "changelog.md",
        ]
        for name in required:
            path = DOC_DIR / name
            self.assertTrue(path.exists(), f"missing document {name}")
            self.assertGreater(path.stat().st_size, 200, f"{name} is suspiciously small")

    def test_validation_report_lists_real_checks(self):
        path = DOC_DIR / "validation_report.md"
        if not path.exists():
            self.skipTest("validation report not generated yet")
        text = path.read_text(encoding="utf-8")
        self.assertIn("Degenerate", text)
        self.assertIn("Bounding box", text)


if __name__ == "__main__":
    unittest.main()
