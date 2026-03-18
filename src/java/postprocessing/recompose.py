import argparse
import json
import os


def get_class_order(schema_data):
    """
    Get the order of classes in the schema based on inheritance.
    """
    dependency_graph = set()  # set of (dependent, dependency) pairs

    for class_ in schema_data["classes"]:
        if schema_data["classes"][class_]["extends"]:
            if schema_data["classes"][class_]["extends"][0] in schema_data["classes"]:
                dependency_graph.add(
                    (class_, schema_data["classes"][class_]["extends"][0])
                )

        if schema_data["classes"][class_]["implements"]:
            for interface in schema_data["classes"][class_]["implements"]:
                if interface in schema_data["classes"]:
                    dependency_graph.add((class_, interface))

        if schema_data["classes"][class_]["nested_inside"]:
            dependency_graph.add(
                (class_, schema_data["classes"][class_]["nested_inside"])
            )

    class_list = topological_sort(dependency_graph)[::-1]

    # check for any classes that were not included in the dependency graph
    class_list += [clz for clz in schema_data["classes"] if clz not in class_list]

    return class_list


def topological_sort(graph: list[tuple[str, str]]) -> list[str]:
    """
    Provides a topological sort of the graph.

    Args:
        graph: A list of tuples where each tuple contains two strings representing the source and target nodes.

    Returns:
        A list of strings representing the nodes in topological order.
    """
    # create a dictionary with the nodes as keys and their dependencies as values
    graph_dict = {}
    for edge in graph:
        if edge[0] not in graph_dict:
            graph_dict[edge[0]] = []
        graph_dict[edge[0]].append(edge[1])

    # create a dictionary with the nodes as keys and their indegree as values
    indegree_dict = {}
    for edge in graph:
        if edge[1] not in indegree_dict:
            indegree_dict[edge[1]] = 0
        if edge[0] not in indegree_dict:
            indegree_dict[edge[0]] = 0
        indegree_dict[edge[1]] += 1

    # create a list of nodes with indegree 0
    zero_indegree = [node for node in indegree_dict if indegree_dict[node] == 0]

    # create a list to store the sorted nodes
    sorted_nodes = []

    # loop over the nodes with indegree 0
    while zero_indegree:
        node = zero_indegree.pop()
        sorted_nodes.append(node)

        # loop over the nodes that depend on the current node
        if node in graph_dict:
            for dependent_node in graph_dict[node]:
                indegree_dict[dependent_node] -= 1
                if indegree_dict[dependent_node] == 0:
                    zero_indegree.append(dependent_node)

    return sorted_nodes


def main(args):

    total_fragments = 0
    total_unsuccessful = 0

    translation_dir = f"data/java/schemas{args.suffix}/translations/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}"

    for schema in os.listdir(translation_dir):

        if not schema.endswith("_cangjie_partial.json"):
            continue

        if args.recompose_evosuite and "ESTest" not in schema:
            continue

        if not args.recompose_evosuite and "ESTest" in schema:
            continue

        data = {}
        with open(f"{translation_dir}/{schema}") as f:
            data = json.load(f)

        # Cangjie: build imports and package declaration
        recomposed_file = ""
        package_name = args.project_name.replace("-", "_")
        recomposed_file += f"package {package_name}\n\n"

        cangjie_imports = data.get("cangjie_imports", [])
        if cangjie_imports:
            recomposed_file += "\n".join(cangjie_imports)
        recomposed_file += "\n\n\n"

        class_order = get_class_order(data)

        for class_ in class_order:

            if "new" in class_ or "{" in class_:  # skip nested and nameless classes
                continue

            # Cangjie class declaration
            cangjie_class_decl = data["classes"][class_].get("cangjie_class_declaration", "")
            if not cangjie_class_decl:
                cangjie_class_decl = f"class {class_} {{\n"
            recomposed_file += cangjie_class_decl

            # Check if class has any fields or methods
            has_fields = data["classes"][class_].get("fields", {}) != {}
            has_methods = data["classes"][class_].get("methods", {}) != {}

            if not has_fields and not has_methods:
                recomposed_file += "    // No fields or methods\n}\n\n"
                continue

            # Process fields
            if has_fields:
                recomposed_file += "    // Class Fields Begin\n"
                for field in data["classes"][class_]["fields"]:
                    field_data = data["classes"][class_]["fields"][field]

                    # Check if translation exists
                    if not field_data.get("translation") or field_data["translation"] == []:
                        # Use partial_translation as fallback
                        partial = field_data.get("partial_translation", [])
                        if partial:
                            field_translation = "\n".join(partial)
                        else:
                            field_translation = f"    // TODO: could not translate field {field}"
                    else:
                        field_translation = "\n".join(field_data["translation"])

                    recomposed_file += f"    {field_translation}\n"
                    total_fragments += 1

                recomposed_file += "    // Class Fields End\n\n"

            # Process methods
            # First, extract main method (Cangjie requires main outside class)
            main_method_translation = None
            if has_methods:
                for method in list(data["classes"][class_]["methods"].keys()):
                    method_key = method.split(":")[1] if ":" in method else method
                    if method_key == "main":
                        method_data = data["classes"][class_]["methods"][method]
                        # Get translation or partial_translation
                        if method_data.get("translation") and method_data["translation"] != []:
                            main_method_translation = "\n".join(method_data["translation"])
                        elif method_data.get("partial_translation"):
                            main_method_translation = "\n".join(method_data["partial_translation"])
                        break

            # Then process other methods
            if has_methods:
                recomposed_file += "    // Class Methods Begin\n"
                for method in data["classes"][class_]["methods"]:
                    method_data = data["classes"][class_]["methods"][method]

                    # Skip overloaded methods unless explicitly requested
                    if (
                        not args.recompose_evosuite
                        and method_data.get("is_overload", False)
                    ):
                        continue

                    # Skip main method (will be added outside class)
                    method_key = method.split(":")[1] if ":" in method else method
                    if method_key == "main":
                        continue

                    # Check if translation exists
                    if not method_data.get("translation") or method_data["translation"] == []:
                        # Use partial_translation as fallback
                        partial = method_data.get("partial_translation", [])
                        if partial:
                            method_translation = "\n".join(partial)
                        else:
                            method_key = method.split(":")[1] if ":" in method else method
                            method_translation = f"    // TODO: could not translate method {method_key}"
                    else:
                        method_translation = "\n".join(method_data["translation"])

                    recomposed_file += f"    {method_translation}\n\n"
                    total_fragments += 1

                recomposed_file += "    // Class Methods End\n"

            # Close class
            recomposed_file += "\n}\n\n"

            # Add main function outside the class (Cangjie requirement)
            if main_method_translation:
                # Remove leading indentation for top-level function
                main_method_translation = main_method_translation.replace("    ", "", 1)
                recomposed_file += main_method_translation + "\n\n"

        formatted_schema_fname = ".".join(schema.split(".")[:-1])
        sub_dir = "/".join(formatted_schema_fname.replace(".", "/").split("/")[1:-1])
        os.makedirs(
            f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/{sub_dir}",
            exist_ok=True,
        )

        if args.recompose_evosuite:
            os.makedirs(
                f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/evosuite-test/{sub_dir}",
                exist_ok=True,
            )
            file_path = f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/evosuite-test/{sub_dir}/{formatted_schema_fname.split('.')[-1].replace('_cangjie_partial', '')}.cj"
        else:
            file_path = f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/{sub_dir}/{formatted_schema_fname.split('.')[-1].replace('_cangjie_partial', '')}.cj"

        recomposed_file = recomposed_file.replace("\u0000", "\\u0000")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(recomposed_file)

        print(f"Generated: {file_path}")

    # Create cjpm.toml for the project
    os.makedirs(
        f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}",
        exist_ok=True,
    )

    cjpm_toml_content = f"""[package]
name = "{args.project_name}"
version = "0.1.0"

[dependencies]
"""

    cjpm_path = f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/cjpm.toml"
    with open(cjpm_path, "w") as f:
        f.write(cjpm_toml_content)

    # Create run.sh for running tests with cjc
    run_sh_content = """#!/bin/bash
CURRENT_DIR=$(pwd)

# Run tests using cjc --test
cjc --test src/test

# Format XML output if needed
if [ -f "test-report.xml" ]; then
    xmllint --format test-report.xml -o test-report.xml
fi
"""

    run_sh_path = f"{args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/run.sh"
    with open(run_sh_path, "w") as f:
        f.write(run_sh_content)

    os.chmod(run_sh_path, 0o755)

    print(f"\nTotal fragments processed: {total_fragments}")
    print(f"Total unsuccessful: {total_unsuccessful}")
    print(f"\nProject ready at: {args.output_dir}/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/")
    print("Run tests with: cd <project> && cjc --test src/test")


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser(
        description="Recompose Cangjie translation results into complete files"
    )
    parser_.add_argument(
        "--project_name",
        type=str,
        dest="project_name",
        help="project name to translate",
    )
    parser_.add_argument(
        "--model_name", type=str, dest="model_name", help="model name to translate"
    )
    parser_.add_argument(
        "--output_dir",
        type=str,
        dest="output_dir",
        help="directory to store recomposed projects",
        default="data/cangjie_projects",
    )
    parser_.add_argument(
        "--type", type=str, dest="type", help="prompting type signature/body"
    )
    parser_.add_argument(
        "--temperature", type=float, dest="temperature", help="temperature for sampling"
    )
    parser_.add_argument(
        "--fragment_name",
        type=str,
        dest="fragment_name",
        help="fragment name to recompose",
    )
    parser_.add_argument(
        "--recompose_evosuite",
        action="store_true",
        dest="recompose_evosuite",
        help="recompose evosuite tests",
    )
    parser_.add_argument(
        "--suffix",
        type=str,
        dest="suffix",
        default="_decomposed_tests",
        help="suffix to add to the recomposed files",
    )
    args = parser_.parse_args()
    main(args)
