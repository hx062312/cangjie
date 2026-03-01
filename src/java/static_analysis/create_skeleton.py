import argparse
import json
import keyword
import os
from collections import defaultdict


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


def get_class_order(schema_data):
    if schema_data["classes"] == {}:
        return []

    graph = []
    for class_ in schema_data["classes"]:
        for parent in schema_data["classes"][class_]["extends"]:
            parent = parent.split("<")[0].replace("new ", "").strip()
            graph.append((parent, class_))

    class_order = topological_sort(graph)
    return class_order


def split_with_nested_commas(s):
    """Split string by comma, but ignore commas inside angle brackets."""
    result = []
    current = ""
    depth = 0

    for char in s:
        if char == "<":
            depth += 1
            current += char
        elif char == ">":
            depth -= 1
            current += char
        elif char == "," and depth == 0:
            result.append(current)
            current = ""
        else:
            current += char

    if current:
        result.append(current)

    return result


def get_dependency_path(dependent_class, project_name, suffix):
    """Get the dependency path for a class."""
    if dependent_class.startswith(project_name):
        return ".".join(dependent_class.split(".")[1:-1])
    else:
        return dependent_class.replace(".", "/")


def remove_duplicate_methods(schema):
    """
    Cangjie supports method overloading natively, so we don't need to
    detect and mark duplicate methods.
    """
    return schema


def get_dependency_cycle(dependencies):
    adjacency_list = defaultdict(list)
    class_path = {}
    for key, value in dependencies.items():
        for pair in value:
            # if pair[0] == '':
            #     continue
            adjacency_list[key].append(pair[0])
            class_path[pair[0]] = pair[1]

    cycles = []
    for k, v in adjacency_list.copy().items():
        for dependency in v:
            if k in adjacency_list[dependency] and (dependency, k) not in cycles:
                cycles.append((k, dependency))

    return cycles, class_path


def has_child_parent_dept(dependent_files, class_path, project_name, suffix):
    verified_dependent_files = []
    for class_1, class_2 in dependent_files:
        class_1_path = get_dependency_path(class_path[class_1], project_name, suffix)
        class_2_path = get_dependency_path(class_path[class_2], project_name, suffix)

        class_1_schema_name = f"data/java/schemas{suffix}/{project_name}/{project_name}.{class_1_path}.json"
        class_2_schema_name = f"data/java/schemas{suffix}/{project_name}/{project_name}.{class_2_path}.json"

        class_1_schema = {}
        with open(class_1_schema_name, "r") as f:
            class_1_schema = json.load(f)

        class_2_schema = {}
        with open(class_2_schema_name, "r") as f:
            class_2_schema = json.load(f)

        for schema_class in class_2_schema["classes"]:
            if class_1 in [
                class_.split("<")[0].replace("new ", "").strip()
                for class_ in class_2_schema["classes"][schema_class]["extends"]
            ]:
                (
                    verified_dependent_files.append(
                        (class_1, class_1_schema_name, class_2, class_2_schema_name, 0)
                    )
                    if (
                        class_1,
                        class_1_schema_name,
                        class_2,
                        class_2_schema_name,
                        0,
                    )
                    not in verified_dependent_files
                    else None
                )
                continue
            if class_1 in [
                class_.split("<")[0].replace("new ", "").strip()
                for class_ in class_2_schema["classes"][schema_class]["implements"]
            ]:
                (
                    verified_dependent_files.append(
                        (class_1, class_1_schema_name, class_2, class_2_schema_name, 0)
                    )
                    if (
                        class_1,
                        class_1_schema_name,
                        class_2,
                        class_2_schema_name,
                        0,
                    )
                    not in verified_dependent_files
                    else None
                )
                continue

    return verified_dependent_files


# Cangjie type mapping
cangjie_type_map = {
    "int": "Int64",
    "long": "Int64",
    "double": "Float64",
    "boolean": "Bool",
    "String": "String",
    "List<T>": "Array<T>",
    "Map<K,V>": "HashMap<K, V>",
    "void": "Unit",
    "byte": "UInt8",
    "short": "Int16",
    "float": "Float32",
}


def get_cangjie_type(java_type, extracted_types):
    """Convert Java type to Cangjie type."""
    if java_type in extracted_types:
        java_type = extracted_types[java_type]

    # Handle generic types
    if "<" in java_type:
        base = java_type.split("<")[0]
        type_params = java_type.split("<")[1].rstrip(">")
        if base == "List" or base == "ArrayList":
            return f"Array<{type_params}>"
        elif base == "Map" or base == "HashMap":
            return f"HashMap<{type_params}>"

    # Simple type mapping
    type_mapping = {
        "int": "Int64",
        "long": "Int64",
        "double": "Float64",
        "boolean": "Bool",
        "String": "String",
        "void": "Unit",
        "byte": "UInt8",
        "short": "Int16",
        "float": "Float32",
    }

    return type_mapping.get(java_type, java_type)


def main(args):

    with open(f"data/java/type_resolution/universal_type_map_final.json", "r") as f:
        extracted_types = json.load(f)

    reserved_tokens = dir(__builtins__) + keyword.kwlist

    # fix
    # extracted_types = {k.split(".")[-1]: v for k, v in extracted_types.items()}
    temp_types = {}
    for k, v in extracted_types.items():
        short_key = k.split(".")[-1]
        if short_key in temp_types and not v:
            continue
        temp_types[short_key] = v
    extracted_types = temp_types

    schemas = os.listdir(f"data/java/schemas{args.suffix}/{args.project_name}")

    dependencies_dir = f"data/java/dependencies{args.suffix}"
    with open(f"{dependencies_dir}/{args.project_name}/dependencies.json", "r") as f:
        dependencies = json.load(f)

    dependent_files, class_path = get_dependency_cycle(dependencies)
    verified_dependent_files = has_child_parent_dept(
        dependent_files, class_path, args.project_name, args.suffix
    )

    for schema_fname in schemas:
        if args.suffix == "_evosuite" and not schema_fname.endswith("ESTest.json"):
            continue

        if args.suffix != "_evosuite" and "ESTest" in schema_fname:
            continue

        schema_path = (
            f"data/java/schemas{args.suffix}/{args.project_name}/{schema_fname}"
        )

        schema = {}
        with open(schema_path, "r") as f:
            schema = json.load(f)

        schema = remove_duplicate_methods(schema)

        # Cangjie uses package declaration instead of imports at the top
        skeleton = "// Package Declaration\npackage "
        # Extract package name from path
        if "src/main/java" in schema["path"]:
            package_name = (
                schema["path"]
                .split("src/main/java/")[1]
                .rsplit("/", 1)[0]
                .replace("/", ".")
            )
        elif "src" in schema["path"]:
            package_name = (
                schema["path"].split("src/")[1].rsplit("/", 1)[0].replace("/", ".")
            )
        else:
            package_name = args.project_name
        skeleton += package_name + "\n\n"

        skeleton += "// Imports Begin\n"
        skeleton += "// Imports End\n\n"

        target_schema = schema.copy()
        cangjie_imports = []
        class_order = get_class_order(schema)

        # If class_order is empty (no inheritance), process all classes
        if not class_order:
            class_order = list(schema["classes"].keys())

        class_dependencies = []
        for class_ in class_order:
            if "new" in class_ or "{" in class_:  # skip nested and nameless classes
                continue

            source_class_declaration = ""
            with open(schema["path"], "r") as f:
                source_class_declaration = "".join(
                    f.readlines()[
                        schema["classes"][class_]["start"]
                        - 1 : schema["classes"][class_]["end"]
                    ]
                )

            if "enum" in source_class_declaration:
                schema["classes"][class_]["is_enum"] = True
            else:
                schema["classes"][class_]["is_enum"] = False

            dependencies.setdefault(class_, [])

            main_class = class_
            if schema["classes"][class_]["nested_inside"] != []:
                main_class = schema["classes"][class_]["nested_inside"]
                dependencies.setdefault(main_class, [])
                dependencies[main_class].append(main_class)

            dependencies[main_class] += schema["classes"][main_class]["nests"]

            if class_ in dependencies:
                class_dependencies.append((schema["path"], dependencies[class_]))

            class_name = class_
            if "<" in class_:
                class_name = class_.split("<")[0].replace("new ", "").strip()
            elif "(" in class_:
                class_name = class_.split("(")[0].replace("new ", "").strip()

            # Cangjie class declaration using < for inheritance
            class_declaration = ""
            exceptional_superclasses = {
                "Comparator",
                "Queue",
                "Comparable",
                "Closeable",
                "Enum",
                "Iterator",
                "Iterable",
                "Supplier",
                "Runnable",
            }

            # Determine class type markers
            is_interface = schema["classes"][class_].get("is_interface", False)
            is_abstract = schema["classes"][class_].get("is_abstract", False)

            if schema["classes"][class_]["extends"] != []:
                schema["classes"][class_]["extends"] = [
                    cls_name.split("<")[0].replace("new ", "").strip()
                    for cls_name in schema["classes"][class_]["extends"]
                ]
                schema["classes"][class_]["extends"] = [
                    cls_name.split("(")[0].replace("new ", "").strip()
                    for cls_name in schema["classes"][class_]["extends"]
                ]
                schema["classes"][class_]["extends"] = [
                    (
                        extracted_types[cls_name]
                        if cls_name in extracted_types and cls_name not in class_path
                        else cls_name
                    )
                    for cls_name in schema["classes"][class_]["extends"]
                ]
                schema["classes"][class_]["extends"] = [
                    cls_name
                    for cls_name in schema["classes"][class_]["extends"]
                    if not any(
                        substring in cls_name for substring in exceptional_superclasses
                    )
                    and cls_name != class_name
                ]

                if is_interface:
                    # Interface in Cangjie
                    class_declaration = (
                        "interface "
                        + class_name
                        + " <:"
                        + ", ".join(schema["classes"][class_]["extends"])
                        + " {\n"
                    )
                elif is_abstract:
                    class_declaration = (
                        "class "
                        + class_name
                        + " <:"
                        + ", ".join(schema["classes"][class_]["extends"])
                        + " {\n"
                    )
                else:
                    class_declaration = (
                        "class "
                        + class_name
                        + " <:"
                        + ", ".join(schema["classes"][class_]["extends"])
                        + " {\n"
                    )

            elif schema["classes"][class_]["implements"] != []:
                schema["classes"][class_]["implements"] = [
                    cls_name.split("<")[0].replace("new ", "").strip()
                    for cls_name in schema["classes"][class_]["implements"]
                ]
                schema["classes"][class_]["implements"] = [
                    cls_name.split("(")[0].replace("new ", "").strip()
                    for cls_name in schema["classes"][class_]["implements"]
                ]
                schema["classes"][class_]["implements"] = [
                    (
                        extracted_types[cls_name]
                        if cls_name in extracted_types and cls_name not in class_path
                        else cls_name
                    )
                    for cls_name in schema["classes"][class_]["implements"]
                ]
                schema["classes"][class_]["implements"] = [
                    cls_name
                    for cls_name in schema["classes"][class_]["implements"]
                    if not any(
                        substring in cls_name for substring in exceptional_superclasses
                    )
                    and cls_name != class_name
                ]

                if is_interface:
                    # Interfaces can only use extends in Java, not implements
                    # Fall through to else branch for interface declaration
                    class_declaration = f"interface {class_name} {{\n"
                elif is_abstract:
                    class_declaration = (
                        "class "
                        + class_name
                        + " <:"
                        + ", ".join(schema["classes"][class_]["implements"])
                        + " {\n"
                    )
                else:
                    class_declaration = (
                        "class "
                        + class_name
                        + " <:"
                        + ", ".join(schema["classes"][class_]["implements"])
                        + " {\n"
                    )

            else:
                if is_interface:
                    class_declaration = f"interface {class_name} {{\n"
                else:
                    class_declaration = f"class {class_name} {{\n"

            # Check for test class
            is_test_class = False
            for method_ in schema["classes"][class_]["methods"]:
                if "Test" in [
                    x.split("(")[0]
                    for x in schema["classes"][class_]["methods"][method_][
                        "annotations"
                    ]
                ]:
                    is_test_class = True
                    break

            # Add @Test decorator for test classes in Cangjie
            if "src.test" in schema_fname and is_test_class:
                class_declaration = "@Test\n" + class_declaration
                if "import testing" not in cangjie_imports:
                    cangjie_imports.append("import testing")

            skeleton += class_declaration

            target_schema["classes"][class_][
                "cangjie_class_declaration"
            ] = class_declaration

            if "static_initializers" in target_schema["classes"][class_]:
                for static_initializer_se in target_schema["classes"][class_][
                    "static_initializers"
                ]:
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["partial_translation"] = []
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["translation"] = []
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["translation_status"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["syntactic_validation"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["field_exercise"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["graal_validation"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["test_execution"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["elapsed_time"] = 0
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["generation_timestamp"] = 0
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["model_name"] = (
                        args.model_name
                        if args.model_name
                        else "deepseek-coder-33b-instruct"
                    )
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["include_implementation"] = (
                        True if args.type == "body" else False
                    )

            is_empty_class = True
            skeleton += "\t// Class Fields Begin\n"
            for field in sorted(schema["classes"][class_]["fields"]):
                is_empty_class = False
                field_name = field.split(":")[1].strip()

                # Determine access modifier
                is_public = (
                    "public" in schema["classes"][class_]["fields"][field]["modifiers"]
                )
                is_private = (
                    "private" in schema["classes"][class_]["fields"][field]["modifiers"]
                )
                is_protected = (
                    "protected"
                    in schema["classes"][class_]["fields"][field]["modifiers"]
                )
                is_static = (
                    "static" in schema["classes"][class_]["fields"][field]["modifiers"]
                )

                # Determine let/var (mutable vs immutable)
                is_final = (
                    "final" in schema["classes"][class_]["fields"][field]["modifiers"]
                )

                # Get field type
                field_type = "<?>"  # placeholder
                assert (
                    len(schema["classes"][class_]["fields"][field]["types"]) == 1
                    or len(schema["classes"][class_]["fields"][field]["types"]) == 0
                )

                if (
                    len(schema["classes"][class_]["fields"][field]["types"]) == 1
                    and schema["classes"][class_]["fields"][field]["types"][0][0]
                    in extracted_types
                ):
                    field_type = extracted_types[
                        schema["classes"][class_]["fields"][field]["types"][0][0]
                    ]
                    field_type = get_cangjie_type(field_type, extracted_types)

                # Build field declaration
                access_modifier = (
                    "public "
                    if is_public
                    else ("protected " if is_protected else "internal ")
                )
                if is_static:
                    access_modifier = "public static " if is_public else ("static ")

                var_keyword = "let " if is_final else "var "

                # Get default value
                field_body = ""
                if "=" not in "".join(
                    schema["classes"][class_]["fields"][field]["body"]
                ):
                    if field_type == "String":
                        field_body = '""'
                    elif field_type in ["Int64", "Int16", "UInt8"]:
                        field_body = "0"
                    elif field_type == "Float64" or field_type == "Float32":
                        field_body = "0.0"
                    elif field_type == "Bool":
                        field_body = "false"
                    elif field_type.startswith("Array"):
                        field_body = "[]"
                    elif field_type.startswith("HashMap"):
                        field_body = "[:]"
                    else:
                        field_body = "?"
                elif "=" in "".join(schema["classes"][class_]["fields"][field]["body"]):
                    if "new ArrayList" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ) or "new LinkedList" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ):
                        field_body = "[]"
                    elif "new LinkedHashMap" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ) or "new HashMap" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ):
                        field_body = "[:]"
                    else:
                        field_body = "?"

                target_schema["classes"][class_]["fields"][field][
                    "partial_translation"
                ] = f"\t{access_modifier}{var_keyword}{field_name}: {field_type} = {field_body}".split(
                    "\n"
                )
                target_schema["classes"][class_]["fields"][field]["translation"] = []
                target_schema["classes"][class_]["fields"][field][
                    "translation_status"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field][
                    "syntactic_validation"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field][
                    "field_exercise"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field][
                    "graal_validation"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field][
                    "test_execution"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field]["elapsed_time"] = 0
                target_schema["classes"][class_]["fields"][field][
                    "generation_timestamp"
                ] = 0
                target_schema["classes"][class_]["fields"][field]["model_name"] = (
                    args.model_name
                    if args.model_name
                    else "deepseek-coder-33b-instruct"
                )
                target_schema["classes"][class_]["fields"][field][
                    "include_implementation"
                ] = (True if args.type == "body" else False)

                skeleton += f"\t{access_modifier}{var_keyword}{field_name}: {field_type} = {field_body}\n"

            skeleton += "\t// Class Fields End\n\n"

            skeleton += "\t// Class Methods Begin\n"
            for method in schema["classes"][class_]["methods"]:
                current_method = []
                method_name = method.split(":")[1].strip()

                if method_name.strip() == "":
                    continue

                if method_name in reserved_tokens:
                    method_name = f"{method_name}_"

                is_empty_class = False

                # Determine access modifier
                is_public = (
                    "public"
                    in schema["classes"][class_]["methods"][method]["modifiers"]
                )
                is_private = (
                    "private"
                    in schema["classes"][class_]["methods"][method]["modifiers"]
                )
                is_protected = (
                    "protected"
                    in schema["classes"][class_]["methods"][method]["modifiers"]
                )
                is_static = (
                    "static"
                    in schema["classes"][class_]["methods"][method]["modifiers"]
                )

                # Build access modifier
                access_modifier = (
                    "public "
                    if is_public
                    else ("protected " if is_protected else "internal ")
                )

                # Handle static methods
                static_prefix = "static " if is_static else ""

                # Check if this is a constructor (method name equals class name)
                is_constructor = class_ == method_name

                # Get return type
                return_type = "Unit"
                if (
                    len(schema["classes"][class_]["methods"][method]["return_types"])
                    == 1
                    and schema["classes"][class_]["methods"][method]["return_types"][0][
                        0
                    ]
                    in extracted_types
                ):
                    return_type = extracted_types[
                        schema["classes"][class_]["methods"][method]["return_types"][0][
                            0
                        ]
                    ]
                    return_type = get_cangjie_type(return_type, extracted_types)

                # Build method parameters
                if len(schema["classes"][class_]["methods"][method]["parameters"]) == 0:
                    if is_constructor:
                        # Constructor
                        skeleton += f"\t{access_modifier}init() {{\n\t\t// TODO\n\t}}\n"
                        current_method.append(f"\t{access_modifier}init() {{")
                    else:
                        if is_static:
                            skeleton += f"\t{access_modifier}{static_prefix}func {method_name}(): {return_type} {{\n\t\t// TODO\n\t}}\n"
                            current_method.append(
                                f"\t{access_modifier}{static_prefix}func {method_name}(): {return_type} {{"
                            )
                        else:
                            skeleton += f"\t{access_modifier}func {method_name}(): {return_type} {{\n\t\t// TODO\n\t}}\n"
                            current_method.append(
                                f"\t{access_modifier}func {method_name}(): {return_type} {{"
                            )
                else:
                    types_ = split_with_nested_commas(
                        schema["classes"][class_]["methods"][method]["signature"][
                            schema["classes"][class_]["methods"][method][
                                "signature"
                            ].find("(")
                            + 1 : schema["classes"][class_]["methods"][method][
                                "signature"
                            ].find(")")
                        ]
                    )
                    parameter_types = []
                    for type_ in types_:
                        if type_.strip() in extracted_types:
                            param_type = extracted_types[type_.strip()]
                            parameter_types.append(
                                get_cangjie_type(param_type, extracted_types)
                            )
                        else:
                            parameter_types.append("?")

                    parameters = schema["classes"][class_]["methods"][method][
                        "parameters"
                    ]
                    param_types = [(x, y) for x, y in zip(parameters, parameter_types)]
                    param_types = [
                        (f"{x}_", y) if x in reserved_tokens else (x, y)
                        for x, y in param_types
                    ]

                    if is_constructor:
                        skeleton += (
                            f"\t{access_modifier}init("
                            + ", ".join([x + f": {y.strip()}" for x, y in param_types])
                            + ") {{\n\t\t// TODO\n\t}}\n"
                        )
                        current_method.append(
                            f"\t{access_modifier}init("
                            + ", ".join([x + f": {y.strip()}" for x, y in param_types])
                            + ") {"
                        )
                    else:
                        if is_static:
                            skeleton += (
                                f"\t{access_modifier}{static_prefix}func {method_name}("
                                + ", ".join(
                                    [x + f": {y.strip()}" for x, y in param_types]
                                )
                                + f"): {return_type} {{\n\t\t// TODO\n\t}}\n"
                            )
                            current_method.append(
                                f"\t{access_modifier}{static_prefix}func {method_name}("
                                + ", ".join(
                                    [x + f": {y.strip()}" for x, y in param_types]
                                )
                                + f"): {return_type} {{"
                            )
                        else:
                            skeleton += (
                                f"\t{access_modifier}func {method_name}("
                                + ", ".join(
                                    [x + f": {y.strip()}" for x, y in param_types]
                                )
                                + f"): {return_type} {{\n\t\t// TODO\n\t}}\n"
                            )
                            current_method.append(
                                f"\t{access_modifier}func {method_name}("
                                + ", ".join(
                                    [x + f": {y.strip()}" for x, y in param_types]
                                )
                                + f"): {return_type} {{"
                            )

                # Handle test methods
                if "src.test" in schema_fname:
                    has_setup_method = False
                    setup_method = ""
                    for m in schema["classes"][class_]["methods"]:
                        if "Before" in [
                            x.split("(")[0]
                            for x in schema["classes"][class_]["methods"][m][
                                "annotations"
                            ]
                        ]:
                            has_setup_method = True
                            setup_method = m
                            break

                    if has_setup_method:
                        schema["classes"][class_]["methods"][method]["calls"].append(
                            [schema_fname.replace(".json", ""), class_, setup_method]
                        )

                current_method.append("\t\t// TODO")
                current_method.append("\t}\n")

                target_schema["classes"][class_]["methods"][method][
                    "partial_translation"
                ] = current_method
                target_schema["classes"][class_]["methods"][method]["translation"] = []
                target_schema["classes"][class_]["methods"][method][
                    "translation_status"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "syntactic_validation"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "field_exercise"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "graal_validation"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "test_execution"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method]["elapsed_time"] = 0
                target_schema["classes"][class_]["methods"][method][
                    "generation_timestamp"
                ] = 0
                target_schema["classes"][class_]["methods"][method]["model_name"] = (
                    args.model_name
                    if args.model_name
                    else "deepseek-coder-33b-instruct"
                )
                target_schema["classes"][class_]["methods"][method][
                    "include_implementation"
                ] = (True if args.type == "body" else False)

            skeleton += "\t// Class Methods End\n\n"
            skeleton += "}\n\n"

            if is_empty_class:
                skeleton += "\t// Empty class body\n"

        # Cangjie import mapping
        import_map = {
            "Path": "import std.fs.*",
            "IOBase": "import std.io.*",
            "StringIO": "import std.io.*",
            "io": "import std.io.*",
            "threading": "import std.concurrency.*",
            "BytesIO": "import std.io.*",
            "TextIOWrapper": "import std.io.*",
            "Number": "import std.math.*",
            "Callable": "import std.functional.*",
            "enum": "import std.enum.*",
            "Type": "import std.reflect.*",
            "Any": "import std.any.*",
            "Iterator": "import std.iterator.*",
            "Iterable": "import std.iterator.*",
            "decimal": "import std.bigint.*",
            "Dict": "import std.collection.*",
            "Array": "import std.collection.*",
            "Union": "import std.*",
            "datetime": "import std.time.*",
            "os": "import std.os.*",
            "pickle": "import std.serialization.*",
            "itertools": "import std.iterator.*",
            "sys": "import std.os.*",
            "collections": "import std.collection.*",
            "uuid": "import std.uuid.*",
            "tempfile": "import std.fs.*",
            "logging": "import std.log.*",
            "Enum": "import std.enum.*",
            "testing": "import testing.*",
        }

        for key in import_map:
            if key in skeleton and import_map[key] not in skeleton:
                skeleton = skeleton.replace(
                    "// Imports Begin\n", "// Imports Begin\n" + import_map[key] + "\n"
                )
                cangjie_imports.append(import_map[key].strip())

        # Handle class dependencies
        for dependency in class_dependencies:
            for dependent_class in dependency[1]:
                if len(dependent_class) != 2:
                    continue

                path = get_dependency_path(
                    dependent_class[1], args.project_name, args.suffix
                )
                skip = False
                for (
                    class_1,
                    class_1_schema_name,
                    class_2,
                    class_2_schema_name,
                    is_child,
                ) in verified_dependent_files:
                    if (
                        is_child == 1
                        and schema_fname == class_2_schema_name.split("/")[-1]
                        and class_1 in path
                    ):
                        skip = True
                        break
                    if (
                        is_child == 0
                        and schema_fname == class_1_schema_name.split("/")[-1]
                        and class_2 in path
                    ):
                        skip = True
                        break

                if skip:
                    continue

                import_stmt = f"import {path}"
                if import_stmt in skeleton:
                    continue
                cangjie_imports.append(import_stmt)
                skeleton = skeleton.replace(
                    "// Imports Begin\n", f"// Imports Begin\n{import_stmt}\n"
                )

        target_schema.setdefault("cangjie_imports", [])

        skeleton_lines = skeleton.split("\n")
        for i in range(len(skeleton_lines)):
            current_line = skeleton_lines[i]
            for exceptional_import in [
                "commons.io",
                "commons.logging",
                "opentest4j",
                "com.google",
                "org.evosuite",
                "scaffolding",
            ]:
                if exceptional_import in current_line:
                    skeleton_lines[i] = f"// {current_line}"
                    if current_line in cangjie_imports:
                        cangjie_imports[cangjie_imports.index(current_line)] = (
                            f"// {current_line}"
                        )
                if (
                    "joda.convert" in current_line and args.project_name == "joda-money"
                ):  # resolving these dependencies later
                    skeleton_lines[i] = f"// {current_line}"
                    for import_ in cangjie_imports:
                        if "joda.convert" in import_ and "//" not in import_:
                            cangjie_imports[cangjie_imports.index(import_)] = (
                                f"// {import_}"
                            )

        target_schema["cangjie_imports"] = cangjie_imports

        skeleton = "\n".join(skeleton_lines)
        formatted_schema_fname = ".".join(schema_fname.split(".")[:-1])

        os.makedirs(f"data/java/skeletons/{args.project_name}", exist_ok=True)

        formatted_schema_fname = ".".join(schema_fname.split(".")[:-1])
        sub_dir = "/".join(formatted_schema_fname.replace(".", "/").split("/")[1:-1])
        os.makedirs(f"data/java/skeletons/{args.project_name}/{sub_dir}", exist_ok=True)

        # Change file extension from .py to .cj
        file_path = f"data/java/skeletons/{args.project_name}/{sub_dir}/{formatted_schema_fname.split('.')[-1]}.cj"
        with open(file_path, "w") as f:
            f.write(skeleton)

        # Note: Cangjie doesn't need black formatting like Python
        # The generated .cj file should be valid Cangjie code

        # add __init__.cj files for each subdirectory (optional for Cangjie)
        sub_dirs = sub_dir.split("/")
        for i in range(len(sub_dirs)):
            current_sub_dir = "/".join(sub_dirs[: i + 1])
            # Cangjie doesn't require __init__.cj files

        os.makedirs(
            f"data/java/schemas{args.suffix}/translations/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}",
            exist_ok=True,
        )
        with open(
            f"data/java/schemas{args.suffix}/translations/{args.model_name}/{args.type}/{args.temperature}/{args.project_name}/{formatted_schema_fname}_cangjie_partial.json",
            "w",
        ) as f:
            json.dump(target_schema, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Cangjie class skeleton")
    parser.add_argument(
        "--project_name", type=str, dest="project_name", help="name of the project"
    )
    parser.add_argument(
        "--model_name", type=str, dest="model_name", help="name of the model"
    )
    parser.add_argument(
        "--type", type=str, dest="type", help="prompt type signature/body"
    )
    parser.add_argument("--suffix", type=str, dest="suffix", help="suffix")
    parser.add_argument(
        "--temperature", type=float, dest="temperature", help="temperature"
    )
    args = parser.parse_args()

    main(args)
