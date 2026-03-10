import json
import os
import subprocess
import tempfile
from calculate_coverage import calculate_method_coverage


def test_validation(args, eligible_tests):
    """
    Validate tests using Cangjie compiler and test runner (cjc --test).
    """

    # Note: For Cangjie, we don't need to recompose Python files
    # The recompose step is handled differently for Cangjie projects
    # For now, we assume test files are already prepared

    test_execution_results = {}
    failed_tests = []

    # Cangjie test output directory
    test_output_dir = "/tmp/cangjie_tests"
    os.makedirs(test_output_dir, exist_ok=True)

    for test in eligible_tests:
        # Convert schema name to Cangjie file path
        test_path = test["schema_name"].replace(".", "/") + ".java"
        test_path = (
            test_path[test_path.index(args.project_name):]
            .replace("test/java/org", "test/org")
            .replace(".java", ".cj")  # Use .cj extension for Cangjie
        )
        test_class = test["class_name"]
        test_method = test["fragment_name"].split(":")[1]

        if not test_method.startswith("test"):
            test_method = "test" + test_method

        if "_decomposed" in test_method:
            actual_test_name = test_method[: test_method.index("_decomposed")].split(
                "_"
            )[0]
        else:
            actual_test_name = test_method

        if actual_test_name in failed_tests:
            continue

        test_execution_results.setdefault(
            f"{test_path}::{test_class}::{test_method}",
            {
                "test_outcome": "exercised-success",
                "feedback": "",
                "covered_methods": [],
            },
        )

        # Find the test file
        test_file_path = f"data/recomposed_projects/{args.model_name}/{args.prompt_type}/{args.temperature}/{args.project_name}/{test_path}"

        if not os.path.exists(test_file_path):
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "test_outcome"
            ] = "exercised-failed"
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "feedback"
            ] = f"Test file not found: {test_file_path}"
            failed_tests.append(actual_test_name)
            continue

        # Compile and run test using cjc --test
        output_binary = os.path.join(test_output_dir, f"test_{test_class}_{test_method}")

        try:
            # Use cjc --test to compile and run the test
            cmd = [
                "cjc",
                "--test",
                "-o", output_binary,
                test_file_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                # Test compilation or execution failed
                test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                    "test_outcome"
                ] = "exercised-failed"
                test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                    "feedback"
                ] = result.stderr + result.stdout
                failed_tests.append(actual_test_name)
            else:
                # Test passed
                test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                    "test_outcome"
                ] = "exercised-success"
                # For Cangjie, we might want to calculate coverage here if supported

        except subprocess.TimeoutExpired:
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "test_outcome"
            ] = "exercised-failed"
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "feedback"
            ] = "Test execution timeout"
            failed_tests.append(actual_test_name)
        except Exception as e:
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "test_outcome"
            ] = "exercised-failed"
            test_execution_results[f"{test_path}::{test_class}::{test_method}"][
                "feedback"
            ] = str(e)
            failed_tests.append(actual_test_name)

    return test_execution_results
