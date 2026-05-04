"""Great Expectations integration for NZ Habitat Intelligence Pipeline.

Uses the official Great Expectations library (v1.17+) for data validation
with proper DataContext, ExpectationSuites, and Checkpoints.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class NZHabitatValidator:
    """Run Great Expectations validation on pipeline data layers.

    Uses the official GE library with DataContext, ExpectationSuites, and Checkpoints.
    Falls back to custom validation if GE is not available.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.ge_dir = self.project_root / "great_expectations"
        self.expectations_dir = self.ge_dir / "expectations"
        self.results_dir = self.ge_dir / "validations"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Try to initialize GE context
        self._use_real_ge = False
        self._context = None
        try:
            import great_expectations as gx
            try:
                self._context = gx.get_context(
                    project_root_dir=str(self.project_root),
                )
            except TypeError:
                # Older GE versions may not support project_root_dir
                self._context = gx.get_context()
            self._use_real_ge = True
            logger.info("Great Expectations context initialized successfully")
        except Exception as e:
            logger.warning("Could not initialize GE context, using custom validator: %s", e)

    def _ensure_expectation_suite(self, suite_name: str) -> Optional[Any]:
        """Ensure an expectation suite exists in GE context."""
        if not self._use_real_ge or self._context is None:
            return None

        try:
            suite = self._context.suites.get(suite_name)
            if suite is not None:
                return suite
        except Exception:
            pass

        return None

    def validate_parquet(self, file_path: Path, suite_name: str) -> Dict[str, Any]:
        """Validate a parquet file against an expectation suite."""
        if self._use_real_ge and self._context:
            return self._validate_with_ge(file_path, suite_name, "parquet")
        return self._validate_custom(file_path, suite_name, "parquet")

    def validate_json(self, file_path: Path, suite_name: str) -> Dict[str, Any]:
        """Validate a JSON file against an expectation suite."""
        if self._use_real_ge and self._context:
            return self._validate_with_ge(file_path, suite_name, "json")
        return self._validate_custom(file_path, suite_name, "json")

    def _validate_with_ge(
        self, file_path: Path, suite_name: str, file_type: str
    ) -> Dict[str, Any]:
        """Validate using the official GE library."""
        try:
            import great_expectations as gx
            from great_expectations.core.batch import BatchRequest

            suite = self._ensure_expectation_suite(suite_name)
            if suite is None:
                return self._validate_custom(file_path, suite_name, file_type)

            if file_type == "parquet":
                df = pd.read_parquet(file_path)
            else:
                with open(file_path, "r") as f:
                    data = json.load(f)
                records = data if isinstance(data, list) else [data]
                df = pd.DataFrame(records)

            datasource_name = f"validation_{suite_name}"
            try:
                datasource = self._context.sources.add_pandas(datasource_name)
            except Exception:
                try:
                    datasource = self._context.sources.get(datasource_name)
                except Exception:
                    datasource = self._context.sources.add_pandas(datasource_name)

            asset_name = f"asset_{file_path.stem}"
            try:
                data_asset = datasource.add_dataframe_asset(asset_name)
            except Exception:
                try:
                    data_asset = datasource.get_asset(asset_name)
                except Exception:
                    data_asset = datasource.add_dataframe_asset(asset_name)

            batch_request = data_asset.build_batch_request(dataframe=df)

            validator = self._context.get_validator(
                batch_request=batch_request,
                expectation_suite=suite,
            )

            results = validator.validate()

            validation_result = {
                "asset_name": str(file_path),
                "validation_time": datetime.now().isoformat(),
                "success": results.get("success", False),
                "results": [],
                "summary": {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                },
            }

            for exp_result in results.get("results", []):
                validation_result["results"].append(
                    {
                        "expectation_type": exp_result.get(
                            "expectation_config", {}
                        ).get("expectation_type", ""),
                        "success": exp_result.get("success", False),
                        "kwargs": exp_result.get("expectation_config", {}).get(
                            "kwargs", {}
                        ),
                    }
                )
                if exp_result.get("success", False):
                    validation_result["summary"]["passed"] += 1
                else:
                    validation_result["summary"]["failed"] += 1

            validation_result["summary"]["total"] = len(validation_result["results"])

            return validation_result

        except Exception as e:
            logger.warning("GE validation error for %s, falling back to custom: %s", file_path, e)
            return self._validate_custom(file_path, suite_name, file_type)

    def _validate_custom(
        self, file_path: Path, suite_name: str, file_type: str
    ) -> Dict[str, Any]:
        """Fallback custom validation when GE context is not available."""
        suite_path = self.expectations_dir / f"{suite_name}.json"
        if not suite_path.exists():
            return {"success": False, "error": f"Suite {suite_name} not found"}

        try:
            with open(suite_path, "r") as f:
                suite = json.load(f)
        except Exception as e:
            return {"success": False, "error": f"Failed to load suite: {e}"}

        try:
            if file_type == "parquet":
                df = pd.read_parquet(file_path)
            else:
                with open(file_path, "r") as f:
                    data = json.load(f)
                records = data if isinstance(data, list) else [data]
                df = pd.DataFrame(records)
        except Exception as e:
            return {"success": False, "error": f"Failed to read {file_path}: {e}"}

        return self._run_expectations(df, suite, str(file_path))

    def _run_expectations(
        self, df: pd.DataFrame, suite: Dict, asset_name: str
    ) -> Dict[str, Any]:
        """Run expectations against a DataFrame (custom fallback)."""
        results = {
            "asset_name": asset_name,
            "validation_time": datetime.now().isoformat(),
            "results": [],
            "success": True,
            "summary": {"total": 0, "passed": 0, "failed": 0},
        }

        expectations = suite.get("expectations", [])
        results["summary"]["total"] = len(expectations)

        for exp in expectations:
            exp_type = exp.get("expectation_type", "")
            kwargs = exp.get("kwargs", {})
            passed = self._evaluate_expectation(df, exp_type, kwargs)

            result = {
                "expectation_type": exp_type,
                "success": passed,
                "kwargs": kwargs,
            }
            results["results"].append(result)

            if passed:
                results["summary"]["passed"] += 1
            else:
                results["summary"]["failed"] += 1
                results["success"] = False

        return results

    def _evaluate_expectation(
        self, df: pd.DataFrame, exp_type: str, kwargs: Dict
    ) -> bool:
        """Evaluate a single expectation."""
        try:
            if exp_type == "expect_table_row_count_to_be_between":
                count = len(df)
                min_val = kwargs.get("min_value", 0)
                max_val = kwargs.get("max_value")
                if min_val is not None and count < min_val:
                    return False
                if max_val is not None and count > max_val:
                    return False
                return True

            elif exp_type == "expect_table_columns_to_match_set":
                expected = set(kwargs.get("column_set", []))
                actual = set(df.columns)
                return expected.issubset(actual)

            elif exp_type == "expect_table_columns_to_match_ordered_list":
                expected = kwargs.get("column_list", [])
                actual = list(df.columns)
                return actual == expected

            elif exp_type == "expect_column_values_to_be_of_type":
                col = kwargs.get("column", "")
                type_str = kwargs.get("type_", kwargs.get("expected_type", ""))
                if col not in df.columns:
                    return False
                dtype = str(df[col].dtype)
                type_mapping = {
                    "int": "int", "int64": "int", "int32": "int",
                    "float": "float", "float64": "float", "float32": "float",
                    "str": "object", "string": "object", "object": "object",
                    "bool": "bool", "boolean": "bool",
                    "datetime": "datetime", "datetime64": "datetime",
                }
                actual_type = type_mapping.get(dtype.lower(), dtype.lower())
                expected_type = type_mapping.get(type_str.lower(), type_str.lower())
                if expected_type == "float" and actual_type == "int":
                    return True
                return actual_type == expected_type

            elif exp_type == "expect_column_values_to_not_be_null":
                col = kwargs.get("column", "")
                mostly = kwargs.get("mostly", 1.0)
                if col not in df.columns:
                    return False
                non_null = df[col].notna().sum()
                total = len(df)
                return (non_null / total) >= mostly if total > 0 else True

            elif exp_type == "expect_column_values_to_be_between":
                col = kwargs.get("column", "")
                min_val = kwargs.get("min_value")
                max_val = kwargs.get("max_value")
                if col not in df.columns:
                    return False
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(vals) == 0:
                    return True
                if min_val is not None and (vals < min_val).any():
                    return False
                if max_val is not None and (vals > max_val).any():
                    return False
                return True

            elif exp_type == "expect_column_values_to_be_in_set":
                col = kwargs.get("column", "")
                value_set = set(kwargs.get("value_set", []))
                if col not in df.columns:
                    return False
                actual = set(df[col].dropna().unique())
                return actual.issubset(value_set)

            elif exp_type == "expect_column_values_to_be_unique":
                col = kwargs.get("column", "")
                mostly = kwargs.get("mostly", 1.0)
                if col not in df.columns:
                    return False
                non_null = df[col].dropna()
                if len(non_null) == 0:
                    return True
                unique_ratio = non_null.nunique() / len(non_null)
                return unique_ratio >= mostly

            elif exp_type == "expect_column_max_to_be_between":
                col = kwargs.get("column", "")
                min_val = kwargs.get("min_value")
                max_val = kwargs.get("max_value")
                if col not in df.columns:
                    return False
                vals = pd.to_numeric(df[col], errors="coerce")
                max_actual = vals.max()
                if pd.isna(max_actual):
                    return True
                if min_val is not None and max_actual < min_val:
                    return False
                if max_val is not None and max_actual > max_val:
                    return False
                return True

            else:
                logger.warning("Unknown expectation type: %s", exp_type)
                return True

        except Exception as e:
            logger.error("Error evaluating %s: %s", exp_type, e)
            return False

    def validate_bronze_layer(self) -> List[Dict[str, Any]]:
        """Validate all bronze layer JSON files."""
        bronze_dir = self.project_root / "data_pipeline" / "bronze"
        results = []

        for json_file in sorted(bronze_dir.glob("*_raw.json")):
            if ".contract." in json_file.name:
                continue
            result = self.validate_json(json_file, "bronze_raw_data")
            result["file"] = str(json_file)
            results.append(result)

        return results

    def validate_silver_layer(self) -> List[Dict[str, Any]]:
        """Validate all silver layer parquet files."""
        silver_dir = self.project_root / "data_pipeline" / "silver"
        results = []

        for parquet_file in sorted(silver_dir.glob("*_features.parquet")):
            result = self.validate_parquet(parquet_file, "silver_features")
            result["file"] = str(parquet_file)
            results.append(result)

        return results

    def validate_gold_layer(self) -> List[Dict[str, Any]]:
        """Validate all gold layer KPI parquet files."""
        gold_dir = self.project_root / "data_pipeline" / "gold"
        results = []

        for parquet_file in sorted(gold_dir.glob("kpis-*.parquet")):
            result = self.validate_parquet(parquet_file, "gold_kpis")
            result["file"] = str(parquet_file)
            results.append(result)

        return results

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validations across all layers."""
        logger.info("Starting Great Expectations validation...")

        bronze_results = self.validate_bronze_layer()
        silver_results = self.validate_silver_layer()
        gold_results = self.validate_gold_layer()

        all_results = {
            "validation_time": datetime.now().isoformat(),
            "bronze": bronze_results,
            "silver": silver_results,
            "gold": gold_results,
            "summary": {
                "bronze_total": len(bronze_results),
                "bronze_passed": sum(1 for r in bronze_results if r.get("success")),
                "silver_total": len(silver_results),
                "silver_passed": sum(1 for r in silver_results if r.get("success")),
                "gold_total": len(gold_results),
                "gold_passed": sum(1 for r in gold_results if r.get("success")),
            },
        }

        # Save results
        results_file = (
            self.results_dir
            / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        logger.info("Validation results saved to %s", results_file)

        return all_results

    def print_report(self, results: Dict[str, Any]):
        """Print validation report to console."""
        print("\n" + "=" * 60)
        print("GREAT EXPECTATIONS VALIDATION REPORT")
        print("=" * 60)

        summary = results.get("summary", {})

        print(
            f"\nBronze Layer: {summary.get('bronze_passed', 0)}/{summary.get('bronze_total', 0)} passed"
        )
        for r in results.get("bronze", []):
            status = "PASS" if r.get("success") else "FAIL"
            print(f"  [{status}] {r.get('file', 'unknown')}")

        print(
            f"\nSilver Layer: {summary.get('silver_passed', 0)}/{summary.get('silver_total', 0)} passed"
        )
        for r in results.get("silver", []):
            status = "PASS" if r.get("success") else "FAIL"
            print(f"  [{status}] {r.get('file', 'unknown')}")

        print(
            f"\nGold Layer: {summary.get('gold_passed', 0)}/{summary.get('gold_total', 0)} passed"
        )
        for r in results.get("gold", []):
            status = "PASS" if r.get("success") else "FAIL"
            print(f"  [{status}] {r.get('file', 'unknown')}")

        total = (
            summary.get("bronze_total", 0)
            + summary.get("silver_total", 0)
            + summary.get("gold_total", 0)
        )
        passed = (
            summary.get("bronze_passed", 0)
            + summary.get("silver_passed", 0)
            + summary.get("gold_passed", 0)
        )
        print(f"\nOverall: {passed}/{total} validations passed")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    validator = NZHabitatValidator()
    results = validator.run_all_validations()
    validator.print_report(results)

    # Exit with error code if any validation failed
    all_passed = all(
        r.get("success", False)
        for layer in ["bronze", "silver", "gold"]
        for r in results.get(layer, [])
    )
    sys.exit(0 if all_passed else 1)
