import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.evaluate_paper_excel import CASES_DIR, compare, prepare, read_csv, score


CASE_ID = "page-01"


class PaperExcelEvaluationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((CASES_DIR / "cases.json").read_text())
        cls.case = cls.cases[CASE_ID]
        cls.expected = CASES_DIR / cls.case["expected"]

    def score_modified(self, modify):
        header, rows = read_csv(self.expected)
        modify(rows)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output.csv"
            with output.open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.DictWriter(stream, fieldnames=header[::-1])
                writer.writeheader()
                writer.writerows(rows)
            result = score(self.case, self.expected, output)
        return {"case": CASE_ID, **result}

    def test_expected_output_and_row_order(self):
        for case in self.cases.values():
            path = CASES_DIR / case["expected"]
            report = score(case, path, path)
            self.assertEqual(report["key_f1"], 1)
            self.assertEqual(report["structure_accuracy"], 1)
            self.assertEqual(report["important_notes_recall"], 1)

        def equivalent(rows):
            rows[0]["row_label"] = "（１）事業 創設認可年月日"
            rows[11]["unit"] = "ｍ３／日"
            rows[4]["row_label"] = "管理 者"
            rows.reverse()

        result = self.score_modified(equivalent)
        self.assertEqual(result["structure_accuracy"], 1)
        self.assertEqual(result["key_f1"], 1)

    def test_missing_duplicate_unknown_and_extra_rows_reduce_scores(self):
        def broken(rows):
            rows[1] = rows[0].copy()
            rows[2]["row_label"] = "?"
            rows[3]["level"] = "5"
            rows[4]["col_code"] = "088"
            rows[9]["notes"] = ""

        result = self.score_modified(broken)
        self.assertEqual(result["keys"]["missing"], ["01/002", "01/005"])
        self.assertEqual(result["keys"]["extra"], ["01/088"])
        self.assertEqual(result["keys"]["duplicates"], {"01/001": 2})
        self.assertEqual(result["unknown_cells"], [{"key": "01/003", "field": "row_label"}])
        self.assertLess(result["key_f1"], 1)
        self.assertLess(result["structure_accuracy"], 1)
        self.assertLess(result["important_notes_recall"], 1)

    def test_same_quality_can_have_different_errors(self):
        def mislabeled_first(rows):
            rows[0]["level"] = "2"

        def mislabeled_second(rows):
            rows[1]["level"] = "2"

        baseline = [self.score_modified(mislabeled_first) for _ in range(3)]
        candidate = [self.score_modified(mislabeled_second) for _ in range(3)]
        result = compare(CASE_ID, baseline, candidate)
        self.assertEqual(result["status"], "at_least_baseline")
        self.assertLess(result["baseline"]["structure_accuracy"], 1)
        self.assertEqual(compare(CASE_ID, baseline, candidate[:2])["status"], "unverified")
        stronger = [self.score_modified(lambda rows: None) for _ in range(3)]
        self.assertEqual(compare(CASE_ID, stronger, candidate)["status"], "below_baseline")

    def test_prepare_does_not_copy_expectations(self):
        with tempfile.TemporaryDirectory() as temp:
            workdir = Path(temp)
            prepare(self.case, workdir)
            self.assertEqual(
                {file.name for file in workdir.iterdir()}, {"input.pdf", "layout.yaml", "prompt.txt"}
            )
            with self.assertRaises(ValueError):
                prepare(self.case, workdir)


if __name__ == "__main__":
    unittest.main()
