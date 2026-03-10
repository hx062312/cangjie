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
from cangjie_compilation_validation import cangjie_compile
from get_reverse_traversal import get_reverse_traversal
from prompt_generator import PromptGenerator
from test_validation import test_validation

from src.compositional_glue_tests.script import ERROR, FAILURE, NOT_EXERCISED, SUCCESS


# 找到可以执行来验证当前方法的测试。
def get_eligible_tests(fragment, processed_fragments, args):

    global_call_graph = {}
    with open(f"data/call_graphs/{args.project_name}/call_graph.json", "r") as f:
        global_call_graph = json.load(f)

    executed_tests = {}
    with open(
        f"data/source_test_execution{args.suffix}/{args.project_name}/tests.json", "r"
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
            test_schema = ".".join(test.split("|")[0].split("/")[2:]).replace(
                ".java", ""
            )
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
            f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json", "r"
        ) as f:
            schema_data = json.load(f)

        if schema_data["classes"][fragment["class_name"]][
            f"{fragment['fragment_type']}s"
        ][fragment["fragment_name"]]["translation_status"] in [
            "attempted",
            "out_of_context",
        ]:
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
    schema_file = f"{args.translation_dir}/{fragment['schema_name']}_cangjie_partial.json"
    with open(schema_file, "r") as f:
        schema_data = json.load(f)

    if update_test_execution:
        # if dict ... update test_execution
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
            translation = schema_data["classes"][fragment["class_name"]][
                f"{fragment['fragment_type']}s"
            ][fragment["fragment_name"]]["partial_translation"]

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

        if isinstance(
            schema_data["classes"][fragment["class_name"]][
                f"{fragment['fragment_type']}s"
            ][fragment["fragment_name"]]["test_execution"],
            dict,
        ):
            pass
        else:
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
        ]["cangjie_compilation"].get("outcome") == "success"
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
        f"data/source_test_execution{args.suffix}/{args.project_name}/coverage.json",
        "r",
    ) as f:
        method_coverage = json.load(f)

    main_class_name = fragment["schema_name"]
    main_class_name = main_class_name[main_class_name.find("src.main") + 9 :].replace(
        ".", "/"
    )
    main_method_name = fragment["fragment_name"].split(":")[1]

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

    assert total_covered < total_executed_tests
    max_budget = max(math.ceil(5 * (total_covered / total_executed_tests)), 2)
    if not feedback:
        return min(5, max_budget)
    else:
        return 1


def get_total_input_tokens(prompt, args, model_info):
    if args.model_name == "gpt-4o-2024-11-20":
        encoding = tiktoken.encoding_for_model("gpt-4o")
        total_tokens = len(encoding.encode(prompt))
    else:  # TODO: add token calculator for open-source models
        encoding = tiktoken.encoding_for_model("gpt-4o")
        total_tokens = len(encoding.encode(prompt))

    return total_tokens


def prompt_model(model_info, client, prompt, total_input_tokens, args):
    max_new_tokens = model_info[args.model_name]["total"] - total_input_tokens
    max_new_tokens = min(max_new_tokens, model_info[args.model_name]["max_new_tokens"])

    completion = client.chat.completions.create(
        model=model_info[args.model_name]["model_id"],
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

    if args.model_name == "deepseek-coder-33b-instruct":
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
        ].get("outcome") == "success"
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


def get_suspiciousness_score(fragment):

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
            for k, v in model_info[args.model_name].items()
            if k in ["api_key", "base_url", "default_headers"]
        }
    )

    if budget == {}:
        adaptive_budget = get_adaptive_budget(fragment, args)
        # Simplified budget: only cangjie_compilation and test_execution
        budget = {
            "cangjie_compilation": adaptive_budget,
            "test_execution": adaptive_budget,
        }
        adaptive_budget_feedback = get_adaptive_budget(fragment, args, feedback=True)
        feedback_budget = {
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

        if args.debug:
            print("=======================PROMPT=======================", flush=True)
            print(prompt, flush=True)
            print(
                "=======================GENERATING=======================", flush=True
            )

        total_input_tokens = get_total_input_tokens(prompt, args, model_info)

        # if prompt size exceeds model token limit, mark translation out_of_context and move on to next fragment
        if total_input_tokens >= model_info[args.model_name]["total"]:
            update_labels(
                args=args,
                fragment=fragment,
                translation=[],
                translation_status="out_of_context",
                cangjie_compilation="pending",
                test_execution="pending",
                elapsed_time=0,
            )
            update_budget(fragment, args, budget, type_="final")
            break

        generation = prompt_model(model_info, client, prompt, total_input_tokens, args)

        if args.debug:
            print(generation, flush=True)
            print("---" * 50, flush=True)
        ############################ </TRANSLATION> ############################

        ############################ <CANGJIE COMPILATION VALIDATION> ############################
        # Cangjie compiler (cjc) performs all three validations in one step:
        # - Parser (syntactic validation)
        # - Semantics (field/type validation)
        # - Code generation (executability validation)
        current_budget = "cangjie_compilation"
        cangjie_compilation_status = "pending"
        status, feedback, message = cangjie_compile(generation, fragment, args)

        if status != SUCCESS:
            if budget[current_budget] - 1 == 0:
                # If compilation fails after all budget attempts, mark as failed
                update_labels(
                    args=args,
                    fragment=fragment,
                    translation=[],
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
            translation_status="attempted",
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
        current_budget = "test_execution"
        if not extracted_eligible_tests:
            eligible_tests = get_eligible_tests(fragment, processed_fragments, args)
            extracted_eligible_tests = True

            # if there are no tests ready to be executed, end the loop and mark the fragment as not-exercised
            if eligible_tests == []:
                update_labels(
                    args=args,
                    fragment=fragment,
                    translation=generation,
                    translation_status="attempted",
                    cangjie_compilation={"outcome": cangjie_compilation_status, "message": message},
                    test_execution="not-exercised",
                    elapsed_time=time.time() - start_time,
                )
                update_budget(fragment, args, budget, type_="final")
                break

            # if there are tests ready to be executed, translate them first
            else:
                for test in eligible_tests:
                    if is_test_already_translated(test, args):
                        executable_eligible_tests.append(test)
                        continue

                    translate(
                        test,
                        args,
                        processed_fragments,
                        recursion_depth=recursion_depth - 1,
                    )

                    if not is_test_parseable(test, args):
                        continue

                    processed_fragments.append(
                        f"{test['schema_name']}|{test['class_name']}|{test['fragment_name']}"
                    )
                    executable_eligible_tests.append(test)

                # if no tests are executable / syntactically correct, end the loop and mark the fragment as not-exercised
                if executable_eligible_tests == []:
                    update_labels(
                        args=args,
                        fragment=fragment,
                        translation=generation,
                        translation_status="attempted",
                        cangjie_compilation={"outcome": cangjie_compilation_status, "message": message},
                        test_execution="not-exercised",
                        elapsed_time=time.time() - start_time,
                    )
                    update_budget(fragment, args, budget, type_="final")
                    break

        # after eligible tests are translated, validate the main method fragment with test validation
        test_execution_details = test_validation(args, executable_eligible_tests)

        requires_reprompt = False
        for test in test_execution_details:
            if test_execution_details[test]["test_outcome"] == "exercised-success":
                for covered_method in test_execution_details[test]["covered_methods"]:
                    covered_method_file = covered_method["file"]
                    covered_method_class = covered_method["class"]
                    covered_method_name = covered_method["method"]

                    update_labels(
                        args=args,
                        fragment={
                            "schema_name": covered_method_file,
                            "class_name": covered_method_class,
                            "fragment_name": covered_method_name,
                            "fragment_type": "method",
                        },
                        translation=[],
                        translation_status=[],
                        cangjie_compilation=[],
                        test_execution={test: test_execution_details[test]},
                        elapsed_time=0,
                        update_test_execution=True,
                    )
                continue

            requires_reprompt = True

            if args.debug:
                print(
                    "=======================TEST VALIDATION FAILED - REPROMPTING=======================",
                    flush=True,
                )

            # heuristic 1: if no methods are covered and test fails, the problem is guaranteed to be in the test method. re-prompt the test method.
            # heuristic 2: if stacktrace shows an AttributeError in the test method, re-prompt the test method only
            if test_execution_details[test][
                "covered_methods"
            ] == [] or test_has_attribute_error(test_execution_details[test]):
                test_fragment = get_test_fragment(test, executable_eligible_tests)
                if test_fragment == {}:
                    continue

                translate(
                    test_fragment,
                    args,
                    processed_fragments,
                    budget=feedback_budget if recursion_depth == 2 else budget,
                    feedback=test_execution_details[test]["feedback"],
                    recursion_depth=recursion_depth - 1,
                )
                continue

            suspicious_methods = {}
            for covered_method in test_execution_details[test]["covered_methods"]:
                covered_method_file = covered_method["file"]
                covered_method_class = covered_method["class"]
                covered_method_name = covered_method["method"]

                update_labels(
                    args=args,
                    fragment={
                        "schema_name": covered_method_file,
                        "class_name": covered_method_class,
                        "fragment_name": covered_method_name,
                        "fragment_type": "method",
                    },
                    translation=[],
                    translation_status="attempted",
                    cangjie_compilation="success",
                    test_execution={test: test_execution_details[test]},
                    elapsed_time=0,
                    update_test_execution=True,
                )

                # Skip fragments that have already passed compilation validation
                # (they were already validated in the compilation step)
                covered_method_schema_data = {}
                with open(
                    f"{args.translation_dir}/{covered_method_file}_cangjie_partial.json",
                    "r",
                ) as f:
                    covered_method_schema_data = json.load(f)

                if covered_method_schema_data["classes"][covered_method_class][
                    "methods"
                ][covered_method_name]["cangjie_compilation"].get("outcome") == "success":
                    continue

                # suspiciousness score = total number of failed tests / total number of tests
                suspicious_methods[
                    f"{covered_method_file}|{covered_method_class}|{covered_method_name}"
                ] = get_suspiciousness_score(
                    fragment={
                        "schema_name": covered_method_file,
                        "class_name": covered_method_class,
                        "fragment_name": covered_method_name,
                        "fragment_type": "method",
                    }
                )

            # extract top-k methods with highest suspiciousness score. make k a hyperparameter later.
            k = 3
            suspicious_methods = {
                k: v
                for k, v in sorted(
                    suspicious_methods.items(), key=lambda item: item[1], reverse=True
                )[:k]
            }

            for suspicious_method in suspicious_methods:
                suspicious_method = {
                    "schema_name": suspicious_method.split("|")[0],
                    "class_name": suspicious_method.split("|")[1],
                    "fragment_name": suspicious_method.split("|")[2],
                    "fragment_type": "method",
                    "is_test_method": (
                        True if "test" in suspicious_method.split("|")[2] else False
                    ),
                }
                translate(
                    suspicious_method,
                    args,
                    processed_fragments,
                    budget=feedback_budget if recursion_depth == 2 else budget,
                    feedback=test_execution_details[test]["feedback"],
                    recursion_depth=recursion_depth - 1,
                )

        if args.debug:
            print(
                "=======================TEST VALIDATION FAILED - REPROMPTING=======================",
                flush=True,
            )
            print("recursion_depth:", recursion_depth, flush=True)
            print("budget:", budget, flush=True)

        if requires_reprompt:
            budget[current_budget] -= 1
            continue

        break
        ############################ </TEST EXECUTION> ############################


def main(args):

    # constant variables
    args.prompt_type = "body" if args.include_implementation else "signature"
    args.translation_dir = f"data/schemas{args.suffix}/translations/{args.model_name}/{args.prompt_type}/{args.temperature}/{args.project_name}"

    # extract the reverse-topological order of fragments based on call graph
    fragment_traversal = get_reverse_traversal(args)

    # extract all pending fragments which require translation
    processed_fragments, pending_fragments = get_pending_fragments(
        fragment_traversal, args
    )

    for fragment in tqdm.tqdm(pending_fragments):
        if fragment in processed_fragments:
            continue

        # if a field is already deterministically translated, update labels and move on
        if is_field_already_translated(fragment, args):
            continue

        # if a fragment requires translation, translate it with LLM
        translate(
            fragment, args, processed_fragments, recursion_depth=args.recursion_depth
        )
        processed_fragments.append(
            f"{fragment['schema_name']}|{fragment['class_name']}|{fragment['fragment_name']}"
        )


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser(
        description="Translate java types to cangjie types"
    )
    parser_.add_argument(
        "--model_name",
        type=str,
        dest="model_name",
        help="model name to use for translation",
    )
    parser_.add_argument(
        "--project_name",
        type=str,
        dest="project_name",
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
