import json
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
VALIDATOR = REPO_ROOT / "scripts" / "validate_portfolio_csv.py"


class ValidatePortfolioCSVTests(unittest.TestCase):
    def run_validator(self, csv_text: str, *args: str) -> subprocess.CompletedProcess[str]:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".csv", delete=False) as tmp:
            tmp.write(csv_text)
            tmp_path = Path(tmp.name)
        try:
            return subprocess.run(
                ["python3", str(VALIDATOR), str(tmp_path), *args],
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_valid_row_passes(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg
            """
        )
        result = self.run_validator(csv_text)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Malformed rows (extra columns): 0", result.stdout)
        self.assertIn("Malformed rows (missing columns): 0", result.stdout)
        self.assertIn("Empty required cells: 0", result.stdout)

    def test_missing_file_returns_code_2(self) -> None:
        missing = Path("/tmp/definitely-missing-cifra-file.csv")
        result = subprocess.run(
            ["python3", str(VALIDATOR), str(missing)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
        self.assertIn("ERROR: file not found", result.stdout)

    def test_missing_required_column_fails(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,local/path.jpg
            """
        )
        result = self.run_validator(csv_text)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("ERROR: missing required columns:", result.stdout)
        self.assertIn("featured_image_primary_url", result.stdout)


    def test_duplicate_headers_fail(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local,post_name
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg,slug-2
            """
        )
        result = self.run_validator(csv_text)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("ERROR: duplicate CSV headers detected:", result.stdout)
        self.assertIn("post_name", result.stdout)

    def test_extra_columns_fail(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg,extra
            """
        )
        result = self.run_validator(csv_text)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("Malformed rows (extra columns): 1", result.stdout)
        self.assertIn("at lines: 2", result.stdout)

    def test_missing_columns_fail(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag
            """
        )
        result = self.run_validator(csv_text)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("Malformed rows (missing columns): 1", result.stdout)
        self.assertIn("at lines: 2", result.stdout)

    def test_duplicate_slug_can_fail_when_flag_enabled(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title 1,dup-slug,<p>x</p>,Cat,tag,https://example.com/1.jpg,local/1.jpg
            portfolio,draft,Title 2,dup-slug,<p>y</p>,Cat,tag,https://example.com/2.jpg,local/2.jpg
            """
        )
        result = self.run_validator(csv_text, "--fail-on-duplicate-slug")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("Duplicate post_name: 1", result.stdout)
        self.assertIn("ERROR: duplicate post_name values detected at lines: 3", result.stdout)

    def test_empty_primary_can_fail_when_flag_enabled(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,,local/path.jpg
            """
        )
        result = self.run_validator(csv_text, "--fail-on-empty-primary-url")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("Empty featured_image_primary_url: 1", result.stdout)
        self.assertIn("ERROR: empty featured_image_primary_url values detected at lines: 2", result.stdout)

    def test_empty_required_cells_can_fail_when_flag_enabled(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,
            """
        )
        result = self.run_validator(csv_text, "--fail-on-empty-required")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("Empty required cells: 2", result.stdout)
        self.assertIn("ERROR: empty values in required columns at 2:post_title, 2:file_path_local", result.stdout)

    def test_multiple_strict_flags_report_multiple_errors(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,,dup,<p>x</p>,Cat,tag,,
            portfolio,draft,Title 2,dup,<p>y</p>,Cat,tag,,local/2.jpg
            """
        )
        result = self.run_validator(
            csv_text,
            "--fail-on-duplicate-slug",
            "--fail-on-empty-primary-url",
            "--fail-on-empty-required",
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("ERROR: duplicate post_name values detected at lines: 3", result.stdout)
        self.assertIn("ERROR: empty featured_image_primary_url values detected at lines: 2, 3", result.stdout)
        self.assertIn("ERROR: empty values in required columns", result.stdout)

    def test_json_output_contains_stats_and_exit_code(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg
            """
        )
        result = self.run_validator(csv_text, "--json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["stats"]["rows_checked"], 1)
        self.assertEqual(payload["errors"], [])

    def test_json_output_reports_missing_file(self) -> None:
        missing = Path("/tmp/definitely-missing-cifra-file.json.csv")
        result = subprocess.run(
            ["python3", str(VALIDATOR), str(missing), "--json"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["exit_code"], 2)
        self.assertIn("ERROR: file not found", payload["errors"][0])

    def test_report_path_writes_json_file(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg
            """
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "reports" / "validator-report.json"
            result = self.run_validator(csv_text, "--report-path", str(report_path))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertTrue(report_path.exists())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["exit_code"], 0)
            self.assertEqual(payload["stats"]["rows_checked"], 1)

    def test_report_path_writes_json_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            missing = Path("/tmp/definitely-missing-cifra-file.report.csv")
            report_path = Path(tmp_dir) / "validator-missing.json"
            result = subprocess.run(
                [
                    "python3",
                    str(VALIDATOR),
                    str(missing),
                    "--report-path",
                    str(report_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertTrue(report_path.exists())
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["exit_code"], 2)
            self.assertIn("ERROR: file not found", payload["errors"][0])

    def test_quiet_mode_suppresses_stdout(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg
            """
        )
        result = self.run_validator(csv_text, "--quiet")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_strict_all_enables_all_strict_checks(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,,dup,<p>x</p>,Cat,tag,,
            portfolio,draft,Title 2,dup,<p>y</p>,Cat,tag,,local/2.jpg
            """
        )
        result = self.run_validator(csv_text, "--strict-all")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("ERROR: duplicate post_name values detected at lines: 3", result.stdout)
        self.assertIn("ERROR: empty featured_image_primary_url values detected at lines: 2, 3", result.stdout)
        self.assertIn("ERROR: empty values in required columns", result.stdout)

    def test_json_and_quiet_are_mutually_exclusive(self) -> None:
        csv_text = textwrap.dedent(
            """\
            post_type,post_status,post_title,post_name,post_content,tax_category,tax_post_tag,featured_image_primary_url,file_path_local
            portfolio,draft,Title,slug,<p>x</p>,Cat,tag,https://example.com/a.jpg,local/path.jpg
            """
        )
        result = self.run_validator(csv_text, "--json", "--quiet")
        self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
        self.assertIn("--json and --quiet cannot be used together", result.stderr)


if __name__ == "__main__":
    unittest.main()
