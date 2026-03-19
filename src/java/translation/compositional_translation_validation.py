import argparse
import datetime
import json
import math
import os
import re
import time

import tiktoken
import tqdm
import yaml
from openai import OpenAI
from cangjie_compilation_validation import cangjie_compilation_validation
from get_reverse_traversal import get_reverse_traversal
from prompt_generator import PromptGenerator
from test_validation import test_validation

# Status constants for translation validation
ERROR = "error"
SUCCESS = "success"
FAILURE = "failure"
NOT_EXERCISED = "not-exercised"


def extract_cangjie_code(
    generation: str, class_name: str = None, method_name: str = None
):
    """
    Extract Cangjie code from markdown code blocks.

    Args:
        generation: LLM response containing markdown code blocks
        class_name: Optional class name to wrap the method in
        method_name: Optional method name to extract (if provided, only extract this method)

    Returns:
        Extracted code or None if not found
    """
    import re

    # Replace cangjie code block markers
    generation = generation.replace("```cangjie", "```")
    generation = generation.replace("```cj", "```")
    generation = generation.replace("```java", "```")

    # Extract code block content
    pattern = r"(?:```\s*)+(.+?)(?:\s*```)+"
    match = re.search(pattern, generation, re.DOTALL)

    if match:
        extracted = match.group(1).strip()

        # If method_name is provided, try to extract only that method
        if method_name:
            extracted = extract_method_from_code(extracted, method_name, class_name)

        # Post-process the extracted code
        extracted = post_process_cangjie_code(extracted, class_name)

        return extracted

    # Try alternative pattern if no code block found
    # Look for anything that looks like Cangjie code (has func, class, let, etc.)
    lines = generation.split("\n")
    code_lines = []
    in_code = False

    for line in lines:
        # Check if line looks like it contains code (starts with whitespace or has common keywords)
        if any(
            keyword in line
            for keyword in [
                "func ",
                "class ",
                "let ",
                "var ",
                "pub ",
                "priv ",
                "import ",
                "package ",
            ]
        ):
            in_code = True
            code_lines.append(line)
        elif in_code and (
            line.strip() == ""
            or line.strip().startswith("//")
            or line.strip().startswith("#")
        ):
            # Allow empty lines and comments in code
            code_lines.append(line)
        elif in_code and not line.startswith(" ") and not line.startswith("\t"):
            # Stop if we hit a non-indented line that's not a comment
            if line.strip():
                break
            code_lines.append(line)

    if code_lines:
        extracted = "\n".join(code_lines).strip()

        # If method_name is provided, try to extract only that method
        if method_name:
            extracted = extract_method_from_code(extracted, method_name, class_name)

        # Post-process the extracted code
        extracted = post_process_cangjie_code(extracted, class_name)

        return extracted

    return None


def extract_method_from_code(
    code: str, method_name: str, class_name: str = None
) -> str:
    """
    Extract a specific method from the generated code.

    Args:
        code: Full generated code
        method_name: Name of the method to extract
        class_name: Optional class name (used to find the method in class context)

    Returns:
        Extracted method code
    """
    import re

    # Clean the method name (remove line numbers like "16-21:div" -> "div")
    clean_method_name = method_name
    if ":" in method_name:
        clean_method_name = method_name.split(":")[-1]

    # Try to find the method using regex
    # Match func declaration: (public/private/protected/static/...) func methodName(...)
    # Also handle constructors: func ClassName(...)
    method_patterns = [
        # Standard method: func methodName(
        rf"(public\s+|private\s+|protected\s+|static\s+|internal\s+|override\s+)*func\s+{re.escape(clean_method_name)}\s*\(",
        # Constructor: func ClassName(
        rf"func\s+{re.escape(clean_method_name)}\s*\(",
    ]

    for pattern in method_patterns:
        match = re.search(pattern, code)
        if match:
            # Found the method, extract from here to the end of the method
            start_pos = match.start()

            # Find the matching closing brace
            # Start from the opening brace of the method
            brace_count = 0
            in_method = False
            end_pos = start_pos

            for i in range(start_pos, len(code)):
                if code[i] == "{":
                    brace_count += 1
                    in_method = True
                elif code[i] == "}":
                    brace_count -= 1
                    if in_method and brace_count == 0:
                        end_pos = i + 1
                        break

            extracted_method = code[start_pos:end_pos].strip()
            return extracted_method

    # If we can't find the method, return the original code
    return code


def post_process_cangjie_code(code: str, class_name: str = None) -> str:
    """
    Post-process extracted Cangjie code to fix common issues.

    Args:
        code: Extracted Cangjie code
        class_name: Optional class name to wrap the method in

    Returns:
        Processed Cangjie code
    """
    import re

    # If extracted code doesn't contain class definition but we have a class_name,
    # wrap the method in a class
    if class_name and "class " not in code:
        if "func " in code:
            # Wrap method in class
            code = f"class {class_name} {{\n{code}\n}}"

    # Fix 1: Replace arrow syntax with colon syntax
    # Pattern: func name(...) -> Type { -> func name(...): Type {
    # This handles cases where LLM uses "->" instead of ":" for return type
    code = re.sub(r"(\bfunc\s+\w+[^:]*)\s*->\s*(\w+)\s*\{", r"\1: \2 {", code)

    # Fix 2: Ensure class definitions are complete (have closing braces)
    # Find all class definitions and ensure they have closing braces
    lines = code.split("\n")
    processed_lines = []
    brace_count = 0
    in_class = False

    for line in lines:
        processed_lines.append(line)

        # Track brace count
        brace_count += line.count("{") - line.count("}")

        # If we were in a class and braces are balanced, ensure we have closing brace
        if "{" in line and "class " in line:
            in_class = True

        # If we've closed all braces and were in a class, add closing brace if missing
        if in_class and brace_count == 0 and "}" not in line:
            # Check if previous line already closed the class
            if processed_lines and "}" not in processed_lines[-1]:
                processed_lines.append("}")

    code = "\n".join(processed_lines)

    # Fix 3: Remove duplicate class declarations that might cause issues
    # If multiple classes are declared without proper closure, fix them
    class_pattern = r"(class\s+\w+\s*\{[^}]*)\n\s*(class\s+\w+\s*\{)"
    code = re.sub(class_pattern, r"\1\n}\n\2", code)

    return code


def add_dummy_main(code: str) -> str:
    """
    Add a dummy main function if not present (required by Cangjie compiler).
    Must be placed at the beginning of the file (before class definitions).
    Cangjie uses 'main()' not 'func main()'.
    """
    import re

    # Check if main function already exists (with any parameters)
    # Match patterns like: main(), main(args: ...), main(args: Array<String>)
    if re.search(r"\bmain\s*\(", code):
        return code

    # Add a dummy main function at the beginning (Cangjie uses main() without func)
    code = (
        """main() {
    return 0
}

"""
        + code
    )
    return code


def extract_code_for_translation(generation: str, fragment: dict, args):
    """
    Extract Cangjie code from markdown and prepare for compilation.

    Args:
        generation: LLM response
        fragment: Fragment information
        args: Command line arguments

    Returns:
        tuple: (success: bool, extracted_code: str or None, feedback: str)
    """
    # Get class name and method name from fragment
    class_name = fragment.get("class_name", None)
    method_name = fragment.get("fragment_name", None)
    fragment_type = fragment.get("fragment_type", "unknown")

    # Extract Cangjie code from markdown, passing class name and method name for filtering
    extracted_code = extract_cangjie_code(generation, class_name, method_name)

    if extracted_code is None:
        print(
            f"[DEBUG] Failed to extract code for {class_name}.{method_name} (type: {fragment_type})"
        )
        return False, None, "the model did not generate any code"

    # Add dummy main function if not present (required by Cangjie compiler)
    extracted_code = add_dummy_main(extracted_code)

    # Basic Cangjie syntax checks
    code_lines = extracted_code.split("\n")

    # Remove empty lines and comments for analysis
    meaningful_lines = [
        line
        for line in code_lines
        if line.strip() and not line.strip().startswith("//")
    ]

    if not meaningful_lines:
        return False, None, "the model did not generate any code"

    # Check that the code has at least some structure
    # Look for common Cangjie keywords
    # Note: 'main(' without 'func' is also valid (main function in Cangjie)
    has_function = any("func " in line or "main(" in line for line in code_lines)
    has_class = any("class " in line for line in code_lines)
    has_var = any("var " in line for line in code_lines)
    has_let = any("let " in line for line in code_lines)

    if not (has_function or has_class or has_var or has_let):
        return (
            False,
            None,
            "the generated code does not appear to be valid Cangjie code",
        )

    # If validation passes, return the extracted code
    return True, extracted_code.split("\n"), None


# 找到可以执行来验证当前方法的测试。
def get_eligible_tests(fragment, processed_fragments, args):

    global_call_graph = {}
    with open(f"data/java/call_graphs/{args.project}/call_graph.json", "r") as f:
        global_call_graph = json.load(f)

    executed_tests = {}
    with open(
        f"data/java/source_test_execution{args.suffix}/{args.project}/tests.json", "r"
    ) as f:
        executed_tests = json.load(f)

    test_focal_method_map = {}
    for class_ in global_call_graph:
        for method_ in global_call_graph[class_]:
            if (
                method_ == "schema_file"
                or "src/test" not in global_call_graph[class_]["schema_file"]
            ):
                continue

            test_method = (
                f"{global_call_graph[class_]['schema_file']}|{class_}|{method_}"
            )

            test_focal_method_map.setdefault(test_method, [])
            for focal_method in global_call_graph[class_][method_]:
                test_focal_method_map[test_method].append(
                    f"{focal_method['schema']}|{focal_method['class']}|{focal_method['method']}"
                )

    executable_tests = []
    for test in test_focal_method_map:
        if (
            f"{fragment['schema_name']}|{fragment['class_name']}|{fragment['fragment_name']}"
            not in test_focal_method_map[test]
        ):
            continue

        if all(
            focal_method in processed_fragments
            for focal_method in test_focal_method_map[test]
            if focal_method
            != f"{fragment['schema_name']}|{fragment['class_name']}|{fragment['fragment_name']}"
        ):
            # Build test schema name from fragment schema_name:
            # HelloWorld.src.main.com.example.helloworld.HelloWorld
            # -> HelloWorld.src.test.com.example.helloworld.HelloWorldTest
            main_schema = fragment["schema_name"]
            # Replace src.main with src.test
            test_schema = main_schema.replace(".src.main.", ".src.test.")
            # Add Test suffix to class name
            test_schema += "Test"

            test_class = test.split("|")[1]
            test_method = test.split("|")[2]

            test_schema_data = {}
            with open(
                f"{args.translation_dir}/{test_schema}_cangjie_partial.json", "r"
            ) as f:
                test_schema_data = json.load(f)
            if test_class not in test_schema_data["classes"]:
                continue
            if test_method not in test_schema_data["classes"][test_class]["methods"]:
                continue
            if "Test" not in [
                x.split("(")[0]
                for x in test_schema_data["classes"][test_class]["methods"][
                    test_method
                ]["annotations"]
            ]:
                continue
            if "Ignore" in [
                x.split("(")[0]
                for x in test_schema_data["classes"][test_class]["methods"][
                    test_method
                ]["annotations"]
            ]:
                continue
            if "Disabled" in [
                x.split("(")[0]
                for x in test_schema_data["classes"][test_class]["methods"][
                    test_method
                ]["annotations"]
            ]:
                continue
            # test_class_path = test_schema[test_schema.find('src.test.')+len('src.test.'):]
            # if test_method.split(':')[1] not in executed_tests[test_class_path]:
            #     continue

            executable_tests.append(
                {
                    "schema_name": test_schema,
                    "class_name": test_class,
                    "fragment_name": test_method,
                    "fragment_type": "method",
                    "is_test_method": True,
                }
            )

    non_decomposed_tests = [
        x for x in executable_tests if "_decomposed" not in x["fragment_name"]
    ]
    executable_tests = [
        x for x in executable_tests if "_decomposed" in x["fragment_name"]
    ]
    executable_tests = sorted(
        executable_tests, key=lambda x: int(x["fragment_name"].split("_")[-2][4:])
    )
    executable_tests = executable_tests + non_decomposed_tests
    return executable_tests


# 提取需要翻译的代码片段。
def get_pending_fragments(fragment_traversal, args):
    """
    Extract all pending fragments which require translation
    """

    processed_fragments, pending_fragments = [], []

    for fragment in fragment_traversal:
        schema_data = {}
        with open(
            f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json",
            "r",
        ) as f:
            schema_data = json.load(f)

        # Check if this is a main method (stored in main_methods, not in classes)
        if fragment["fragment_name"] == "main":
            # main is stored in main_methods
            if "main_methods" in schema_data and "main" in schema_data["main_methods"]:
                frag_info = schema_data["main_methods"]["main"]
            else:
                # main not found, skip
                continue
        else:
            frag_info = schema_data["classes"][fragment["class_name"]][
                f"{fragment['fragment_type']}s"
            ][fragment["fragment_name"]]

        translation_status = frag_info.get("translation_status", "")
        translation = frag_info.get("translation", [])

        # Only consider as processed if translation is completed and has content
        if translation_status == "completed" and translation:
            processed_fragments.append(
                f"{fragment['schema_name']}|{fragment['class_name']}|{fragment['fragment_name']}"
            )
            continue

        pending_fragments.append(fragment)

    return processed_fragments, pending_fragments


# 更新 schema 文件中的翻译结果和状态
def update_labels(
    args,
    fragment,
    translation,
    translation_status,
    cangjie_compilation,
    test_execution,
    elapsed_time,
    update_test_execution=False,
):
    """
    Update the labels of the fragment in the schema file.
    For Cangjie: replaces syntactic_validation, field_exercise, graal_validation with cangjie_compilation.
    """
    schema_data = {}
    # Use cangjie file instead of python
    schema_file = (
        f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json"
    )
    with open(schema_file, "r") as f:
        schema_data = json.load(f)

    # Handle main_methods (main function outside class)
    # Use fragment_name because main is always in main_methods, not classes
    is_main = fragment["fragment_name"] == "main"

    if update_test_execution:
        # if dict ... update test_execution
        if is_main:
            if isinstance(
                schema_data["main_methods"][fragment["fragment_name"]]["test_execution"],
                dict,
            ):
                schema_data["main_methods"][fragment["fragment_name"]]["test_execution"].update(test_execution)
            else:
                schema_data["main_methods"][fragment["fragment_name"]]["test_execution"] = test_execution
        else:
            if isinstance(
                schema_data["classes"][fragment["class_name"]]["methods"][
                    fragment["fragment_name"]
                ]["test_execution"],
                dict,
            ):
                schema_data["classes"][fragment["class_name"]]["methods"][
                    fragment["fragment_name"]
                ]["test_execution"].update(test_execution)
            else:
                schema_data["classes"][fragment["class_name"]]["methods"][
                    fragment["fragment_name"]
                ]["test_execution"] = test_execution
    else:
        if translation == "<translated>":
            if is_main:
                fragment_data = schema_data["main_methods"][fragment["fragment_name"]]
            else:
                fragment_data = schema_data["classes"][fragment["class_name"]][
                    f"{fragment['fragment_type']}s"
                ][fragment["fragment_name"]]
            if "partial_translation" not in fragment_data:
                print(
                    f"[DEBUG] partial_translation not found for {fragment['class_name']}.{fragment['fragment_name']}, using empty list"
                )
            translation = fragment_data.get("partial_translation", [])

        if is_main:
            schema_data["main_methods"][fragment["fragment_name"]]["translation"] = translation
            schema_data["main_methods"][fragment["fragment_name"]]["translation_status"] = translation_status
            schema_data["main_methods"][fragment["fragment_name"]]["cangjie_compilation"] = cangjie_compilation

            # Check if test_execution exists before accessing
            fragment_data = schema_data["main_methods"][fragment["fragment_name"]]
            if "test_execution" in fragment_data and (
                isinstance(fragment_data["test_execution"], dict) or
                fragment_data["test_execution"] in ("pending", "not-exercised")
            ):
                pass
            else:
                print(
                    f"[DEBUG] Adding missing test_execution for main.{fragment['fragment_name']}"
                )
                schema_data["main_methods"][fragment["fragment_name"]]["test_execution"] = test_execution
            schema_data["main_methods"][fragment["fragment_name"]]["elapsed_time"] = elapsed_time
            schema_data["main_methods"][fragment["fragment_name"]]["generation_timestamp"] = datetime.datetime.now().isoformat()
        else:
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ]["translation"] = translation
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ]["translation_status"] = translation_status

            # Use cangjie_compilation instead of three separate validations
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ]["cangjie_compilation"] = cangjie_compilation

            # Check if test_execution exists before accessing
            fragment_data = schema_data["classes"][fragment["class_name"]][
                f"{fragment['fragment_type']}s"
            ][fragment["fragment_name"]]
            if "test_execution" in fragment_data and (
                isinstance(fragment_data["test_execution"], dict) or
                fragment_data["test_execution"] in ("pending", "not-exercised")
            ):
                pass
            else:
                print(
                    f"[DEBUG] Adding missing test_execution for {fragment['class_name']}.{fragment['fragment_name']}"
                )
                schema_data["classes"][fragment["class_name"]][
                    f"{fragment['fragment_type']}s"
                ][fragment["fragment_name"]]["test_execution"] = test_execution
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ]["elapsed_time"] = elapsed_time
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ]["generation_timestamp"] = datetime.datetime.now().isoformat()

    with open(schema_file, "w") as f:
        json.dump(schema_data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())


def update_budget(fragment, args, budget, type_="original"):
    schema_data = {}
    with open(
        f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json", "r"
    ) as f:
        schema_data = json.load(f)

    # Handle main_methods (main function outside class)
    # Check if fragment exists in classes, otherwise try main_methods
    if fragment["fragment_name"] == "main":
        # main is in main_methods, not classes
        if "main_methods" in schema_data and "main" in schema_data["main_methods"]:
            schema_data["main_methods"]["main"][f"{type_}_budget"] = budget
        else:
            # Fallback: main might be stored as a regular method in a class
            schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
                fragment["fragment_name"]
            ][f"{type_}_budget"] = budget
    else:
        schema_data["classes"][fragment["class_name"]][f"{fragment['fragment_type']}s"][
            fragment["fragment_name"]
        ][f"{type_}_budget"] = budget

    with open(
        f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json", "w"
    ) as f:
        json.dump(schema_data, f, indent=4)
        f.flush()
        os.fsync(f.fileno())


def is_field_already_translated(fragment, args):
    """
    Check if a field is already deterministically translated
    """
    prompt_generator = PromptGenerator(
        is_feedback=False, args=args, fragment_details=fragment
    )

    if (
        fragment["fragment_type"] == "field"
        and prompt_generator.prompt_status == "translated"
    ):
        update_budget(
            fragment,
            args,
            budget={
                "cangjie_compilation": -1,
                "test_execution": -1,
            },
            type_="original",
        )
        update_budget(
            fragment,
            args,
            budget={
                "cangjie_compilation": -1,
                "test_execution": -1,
            },
            type_="final",
        )
        update_labels(
            args=args,
            fragment=fragment,
            translation=f"<{prompt_generator.prompt_status}>",
            translation_status="attempted",
            cangjie_compilation="success",
            test_execution="pending",
            elapsed_time=0,
        )
        return True

    return False


def is_test_already_translated(test, args):
    """
    Check if a test is already translated and syntactically correct
    """
    test_schema_data = {}
    with open(
        f"{args.translation_dir}/{test['schema_name']}_cangjie_partial.json", "r"
    ) as f:
        test_schema_data = json.load(f)

    if (
        test_schema_data["classes"][test["class_name"]]["methods"][
            test["fragment_name"]
        ]["cangjie_compilation"].get("outcome")
        == "success"
    ):
        return True

    return False


# 根据动态分析自适应调整重试预算
def get_adaptive_budget(fragment, args, feedback=False):
    """
    Get adaptive budget for translation based on dynamic analysis.
    For Cangjie: only cangjie_compilation and test_execution budgets.

    1. Fields and static initializers: 2-3 attempts
    2. Test methods: 2-3 attempts
    3. Main methods: based on test coverage
    """
    if fragment["fragment_type"] in ["field", "static_initializer"]:
        return 2 if not feedback else 1
    elif fragment["fragment_type"] == "method" and fragment["is_test_method"]:
        return 2 if not feedback else 1

    # For main methods, calculate based on test coverage
    method_coverage = {}
    with open(
        f"data/java/source_test_execution{args.suffix}/{args.project}/coverage.json",
        "r",
    ) as f:
        method_coverage = json.load(f)

    main_class_name = fragment["schema_name"]
    main_class_name = main_class_name[main_class_name.find("src.main") + 9 :].replace(
        ".", "/"
    )
    # Handle main method (stored as "main" not "start-end:main")
    if ":" in fragment["fragment_name"]:
        main_method_name = fragment["fragment_name"].split(":")[1]
    else:
        main_method_name = fragment["fragment_name"]

    total_executed_tests = 0
    total_covered = 0

    for test_class in method_coverage:
        for test_method in method_coverage[test_class]:
            total_executed_tests += 1
            if main_class_name in method_coverage[test_class][test_method]:
                if (
                    main_method_name
                    in method_coverage[test_class][test_method][main_class_name]
                ):
                    total_covered += (
                        1
                        if main_method_name
                        in method_coverage[test_class][test_method][main_class_name]
                        else 0
                    )

    # For Cangjie: if all tests cover the method, use max budget
    if total_executed_tests == 0 or total_covered >= total_executed_tests:
        max_budget = 5
    else:
        max_budget = max(math.ceil(5 * (total_covered / total_executed_tests)), 2)
    if not feedback:
        return min(5, max_budget)
    else:
        return 1


def get_total_input_tokens(prompt, args, model_info):
    if args.model == "gpt-4o-2024-11-20":
        encoding = tiktoken.encoding_for_model("gpt-4o")
        total_tokens = len(encoding.encode(prompt))
    else:  # TODO: add token calculator for open-source models
        encoding = tiktoken.encoding_for_model("gpt-4o")
        total_tokens = len(encoding.encode(prompt))

    return total_tokens


def prompt_model(model_info, client, prompt, total_input_tokens, args):
    max_new_tokens = model_info[args.model]["total"] - total_input_tokens
    max_new_tokens = min(max_new_tokens, model_info[args.model]["max_new_tokens"])

    completion = client.chat.completions.create(
        model=model_info[args.model]["model_id"],
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_new_tokens,
        temperature=args.temperature,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    generation = completion.choices[0].message.content

    if args.model == "deepseek-coder-33b-instruct":
        if generation.strip().startswith("```"):
            pass
        elif generation.count("```") % 2 == 0:
            pass
        else:
            generation = prompt + generation.strip()
            generation = generation[generation.find("### Response:") :]

    return generation


def is_test_parseable(test, args):
    """
    Check if a test is translated properly
    """
    schema_data = {}
    with open(
        f"{args.translation_dir}/{test['schema_name']}_cangjie_partial.json", "r"
    ) as f:
        schema_data = json.load(f)

    if (
        schema_data["classes"][test["class_name"]]["methods"][test["fragment_name"]][
            "cangjie_compilation"
        ].get("outcome")
        == "success"
    ):
        return True

    return False


def get_test_fragment(test, executable_eligible_tests):
    test_fragment = {}
    for test_ in executable_eligible_tests:
        test_schema = test.split("::")[0].replace("/", ".").replace(".py", "")
        test_class = test.split("::")[1]
        test_method = test.split("::")[2]

        if (
            test_schema == test_["schema_name"]
            and test_class == test_["class_name"]
            and test_method == test_["fragment_name"].split(":")[1]
        ):
            test_fragment = test_
            break

    return test_fragment


def test_has_attribute_error(test_execution_details):
    # Regular expression to match the AttributeError
    error_regex = r"AttributeError: (.+)"
    method_regex = r"File \"(.+)\", line \d+, in (\w+)"

    error_message = None
    filepath = None
    method_name = None
    traceback_str = test_execution_details["feedback"]

    lines = traceback_str.strip().splitlines()

    for i, line in enumerate(lines):
        # Match the error message
        error_match = re.search(error_regex, line)
        if error_match:
            error_message = "AttributeError: " + error_match.group(1)

        # Match the method name and file path
        method_match = re.search(method_regex, line)
        if method_match:
            filepath = method_match.group(1)
            method_name = method_match.group(2)

    if "_decomposed" not in method_name or "test" not in method_name:
        return False

    if "src/test" in filepath and (error_message and "AttributeError" in error_message):
        return True

    return False


def get_suspiciousness_score(fragment, args):

    schema_data = {}
    with open(
        f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json", "r"
    ) as f:
        schema_data = json.load(f)

    total_tests = 0
    failed_tests = 0

    if isinstance(
        schema_data["classes"][fragment["class_name"]]["methods"][
            fragment["fragment_name"]
        ]["test_execution"],
        dict,
    ):
        for test in schema_data["classes"][fragment["class_name"]]["methods"][
            fragment["fragment_name"]
        ]["test_execution"]:
            total_tests += 1
            if (
                schema_data["classes"][fragment["class_name"]]["methods"][
                    fragment["fragment_name"]
                ]["test_execution"][test]["test_outcome"]
                == "exercised-failed"
            ):
                failed_tests += 1

    if total_tests == 0:
        return 0.0
    return failed_tests / total_tests


def translate(
    fragment, args, processed_fragments, budget={}, feedback=None, recursion_depth=2
):

    if recursion_depth == 0:
        return

    model_info = yaml.safe_load(open("configs/model_configs.yaml", "r"))["models"]

    client = OpenAI(
        **{
            k: v
            for k, v in model_info[args.model].items()
            if k in ["api_key", "base_url", "default_headers"]
        }
    )

    if budget == {}:
        adaptive_budget = get_adaptive_budget(fragment, args)
        # Simplified budget: includes syntactic, cangjie_compilation and test_execution
        budget = {
            "syntactic": adaptive_budget,
            "cangjie_compilation": adaptive_budget,
            "test_execution": adaptive_budget,
        }
        adaptive_budget_feedback = get_adaptive_budget(fragment, args, feedback=True)
        feedback_budget = {
            "syntactic": adaptive_budget_feedback,
            "cangjie_compilation": adaptive_budget_feedback,
            "test_execution": adaptive_budget_feedback,
        }

        update_budget(fragment, args, budget, type_="original")

    current_budget = "cangjie_compilation"
    start_time = time.time()
    extracted_eligible_tests = False
    eligible_tests = []
    executable_eligible_tests = []

    while budget[current_budget] > 0:
        ############################ <TRANSLATION> ############################
        prompt_gen = PromptGenerator(
            is_feedback=True if feedback else False,
            args=args,
            fragment_details=fragment,
            feedback=feedback,
        )
        prompt = prompt_gen.generate_prompt()

        # Commented out to reduce output - uncomment for debugging
        if args.debug:
            print("=======================PROMPT=======================", flush=True)
            print(prompt, flush=True)
            print(
                "=======================GENERATING=======================", flush=True
            )

        total_input_tokens = get_total_input_tokens(prompt, args, model_info)

        # if prompt size exceeds model token limit, mark translation out_of_context and keep previous translation
        if total_input_tokens >= model_info[args.model]["total"]:
            update_labels(
                args=args,
                fragment=fragment,
                translation="<translated>",
                translation_status="out_of_context",
                cangjie_compilation="pending",
                test_execution="pending",
                elapsed_time=0,
            )
            update_budget(fragment, args, budget, type_="final")
            break

        generation = prompt_model(model_info, client, prompt, total_input_tokens, args)

        # Only show generation in debug mode
        if args.debug:
            print(generation, flush=True)
            print("---" * 50, flush=True)
        ############################ </TRANSLATION> ############################

        ############################ <EXTRACT CODE> ############################
        # Extract Cangjie code from markdown
        syntactic_status, extracted_code, syntactic_feedback = (
            extract_code_for_translation(generation, fragment, args)
        )

        if not syntactic_status:
            if budget["syntactic"] - 1 == 0:
                # If code extraction fails after all budget attempts, keep the previous translation
                # instead of clearing it
                update_labels(
                    args=args,
                    fragment=fragment,
                    translation="<translated>",
                    translation_status="attempted",
                    cangjie_compilation={
                        "outcome": "error",
                        "message": syntactic_feedback,
                    },
                    test_execution="pending",
                    elapsed_time=time.time() - start_time,
                )
                update_budget(fragment, args, budget, type_="final")
                break

            budget["syntactic"] -= 1
            if args.debug:
                print(
                    "=======================CODE EXTRACTION FAILED - REPROMPTING=======================",
                    f"Feedback: {syntactic_feedback}",
                    flush=True,
                )
            continue

        # Use extracted code for compilation
        # Convert string to list of lines (each line is an element)
        if isinstance(extracted_code, str):
            # Split into lines - each line becomes an element in the list
            generation_lines = extracted_code.split("\n")
        else:
            generation_lines = extracted_code

        # Convert list of lines back to full code format expected by compiler
        generation = "\n".join(generation_lines)

        # Initialize budget for syntactic if not exists
        if "syntactic" not in budget:
            budget["syntactic"] = 2

        update_labels(
            args=args,
            fragment=fragment,
            translation=generation_lines,
            translation_status="attempted",
            cangjie_compilation={
                "outcome": "pending",
                "message": "waiting for compilation",
            },
            test_execution="pending",
            elapsed_time=time.time() - start_time,
        )
        ############################ </EXTRACT CODE> ############################

        ############################ <CANGJIE COMPILATION VALIDATION> ############################
        # Cangjie compiler (cjc) performs all three validations in one step:
        # - Parser (syntactic validation)
        # - Semantics (field/type validation)
        # - Code generation (executability validation)
        current_budget = "cangjie_compilation"
        cangjie_compilation_status = "pending"
        status, feedback, message = cangjie_compilation_validation(generation, fragment, args)

        if status != SUCCESS:
            if budget[current_budget] - 1 == 0:
                # If compilation fails after all budget attempts, keep the previous translation
                # instead of clearing it
                update_labels(
                    args=args,
                    fragment=fragment,
                    translation="<translated>",
                    translation_status="attempted",
                    cangjie_compilation={"outcome": "error", "message": message},
                    test_execution="pending",
                    elapsed_time=time.time() - start_time,
                )
                update_budget(fragment, args, budget, type_="final")
                break

            if args.debug:
                print(
                    "=======================CANGJIE COMPILATION FAILED - REPROMPTING=======================",
                    f"Feedback: {feedback}",
                    flush=True,
                )

            budget[current_budget] -= 1
            continue

        # Compilation succeeded
        cangjie_compilation_status = "success"
        update_labels(
            args=args,
            fragment=fragment,
            translation=generation,
            translation_status="completed",
            cangjie_compilation={"outcome": "success", "message": message},
            test_execution="pending",
            elapsed_time=time.time() - start_time,
        )
        update_budget(fragment, args, budget, type_="final")

        # For test methods, return after successful compilation
        if fragment["is_test_method"]:
            return

        # For fields and static initializers, compilation success is sufficient
        if fragment["fragment_type"] in ["field", "static_initializer"]:
            break
        ############################ </CANGJIE COMPILATION VALIDATION> ############################

        ############################ <TEST EXECUTION> ############################
        # TODO: 重构测试执行逻辑 - 临时跳过
        current_budget = "test_execution"

        # 临时占位: 编译成功后直接标记为 completed，不执行测试
        update_labels(
            args=args,
            fragment=fragment,
            translation=generation,
            translation_status="completed",
            cangjie_compilation={
                "outcome": "success",
                "message": message,
            },
            test_execution="not-exercised",
            elapsed_time=time.time() - start_time,
        )
        update_budget(fragment, args, budget, type_="final")
        break
        ############################ </TEST EXECUTION> ############################


def handle_main_for_schema(schema_name, args, processed_fragments):
    """
    Check if a schema has a main function that needs translation and translate it.

    Args:
        schema_name: The schema name (e.g., HelloWorld.src.main.com.example.helloworld.HelloWorld)
        args: Command line arguments
        processed_fragments: List of already processed fragments
    """
    schema_file = f"{schema_name}_cangjie_partial.json"
    schema_path = os.path.join(args.translation_dir, schema_file)

    if not os.path.exists(schema_path):
        return

    with open(schema_path, 'r') as f:
        schema_data = json.load(f)

    if "main_methods" not in schema_data or "main" not in schema_data["main_methods"]:
        return

    main_info = schema_data["main_methods"]["main"]
    if main_info.get("translation_status") in ["completed", "attempted", "out_of_context"]:
        return

    print(f"[DEBUG] Translating main for schema {schema_name}", flush=True)
    main_fragment = {
        "schema_name": schema_name,
        "class_name": "main",
        "fragment_name": "main",
        "fragment_type": "method",
        "is_test_method": False,
    }
    translate(main_fragment, args, processed_fragments, recursion_depth=args.recursion_depth)
    processed_fragments.append(f"{schema_name}|main|main")


def cleanup_dummy_main_functions(args):
    """
    Clean up dummy main functions from skeleton files after all translations.

    Dummy mains are top-level main functions in test files that are placeholders
    (marked with "// dummy main"). These should be removed.
    """
    skeleton_base = f"data/java/skeletons/translations/{args.model}/{args.prompt_type}/{args.temperature}/{args.project}"

    if not os.path.exists(skeleton_base):
        return

    # Walk through all .cj files in skeleton directory
    for root, _, files in os.walk(skeleton_base):
        for filename in files:
            if not filename.endswith('.cj'):
                continue

            filepath = os.path.join(root, filename)
            with open(filepath, 'r') as f:
                content = f.read()

            # Pattern to find dummy main function: has "// dummy main" comment
            dummy_main_pattern = r'\nmain\s*\([^)]*\)\s*:\s*[^\{]*\{[^}]*//\s*dummy\s+main[^}]*\}'

            # Check if it's a dummy main
            if re.search(dummy_main_pattern, content, re.DOTALL):
                new_content = re.sub(dummy_main_pattern, '', content, flags=re.DOTALL)
                new_content = new_content.rstrip()
                with open(filepath, 'w') as f:
                    f.write(new_content)
                print(f"[DEBUG] Removed dummy main from: {filepath}", flush=True)


def main(args):

    # constant variables
    args.prompt_type = "body" if args.include_implementation else "signature"
    args.translation_dir = f"data/java/schemas{args.suffix}/translations/{args.model}/{args.prompt_type}/{args.temperature}/{args.project}"

    # extract the reverse-topological order of fragments based on call graph
    fragment_traversal = get_reverse_traversal(args)

    # extract all pending fragments which require translation
    processed_fragments, pending_fragments = get_pending_fragments(
        fragment_traversal, args
    )

    for fragment in tqdm.tqdm(pending_fragments):
        frag_key = f"{fragment['schema_name']}|{fragment['class_name']}|{fragment['fragment_name']}"
        if frag_key in processed_fragments:
            continue

        # if a field is already deterministically translated, update labels and move on
        # Skip this check for main methods (they are in main_methods, not classes)
        if fragment["fragment_type"] == "field":
            if is_field_already_translated(fragment, args):
                processed_fragments.append(frag_key)
                continue

        # translate with LLM
        translate(
            fragment, args, processed_fragments, recursion_depth=args.recursion_depth
        )
        processed_fragments.append(frag_key)

        # After translating, cleanup dummy main functions
        cleanup_dummy_main_functions(args)

    # Final cleanup
    cleanup_dummy_main_functions(args)


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser(
        description="Translate java types to cangjie types"
    )
    parser_.add_argument(
        "--model",
        type=str,
        dest="model",
        help="model name to use for translation",
    )
    parser_.add_argument(
        "--project",
        type=str,
        dest="project",
        help="project name to translate",
    )
    parser_.add_argument(
        "--from_lang", type=str, dest="from_lang", help="language to translate from"
    )
    parser_.add_argument(
        "--to_lang", type=str, dest="to_lang", help="language to translate to"
    )
    parser_.add_argument(
        "--include_call_graph",
        action="store_true",
        help="include call graph in translation",
    )
    parser_.add_argument(
        "--include_implementation",
        action="store_true",
        help="include implementation of dependent methods",
    )
    parser_.add_argument(
        "--validate_by_cangjie",
        action="store_true",
        help="validate translation by Cangjie compiler",
    )
    parser_.add_argument(
        "--translate_evosuite",
        action="store_true",
        help="translate evosuite generated tests",
    )
    parser_.add_argument("--debug", action="store_true", help="debug mode")
    parser_.add_argument(
        "--temperature",
        type=float,
        dest="temperature",
        help="temperature for generation",
    )
    parser_.add_argument(
        "--suffix", type=str, dest="suffix", help="suffix for the translated files"
    )
    parser_.add_argument(
        "--recursion_depth",
        type=int,
        dest="recursion_depth",
        help="depth of recursion for translation",
    )
    args = parser_.parse_args()
    main(args)
