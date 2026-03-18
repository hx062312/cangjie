import argparse
import json
import keyword
import os
from collections import defaultdict


def calculate_output_path(
    formatted_schema_fname: str,
    class_name: str,
    project: str,
    is_test: bool,
    src_dir: str,
) -> str:
    """
    Calculate the output file path for a Cangjie skeleton file.

    Args:
        formatted_schema_fname: Schema filename without extension (e.g., commons-fileupload.src.main.org.apache.commons.fileupload.disk.DiskFileItem)
        class_name: Name of the class (e.g., DiskFileItem)
        project: Name of the project (e.g., commons-fileupload)
        is_test: Whether this is a test file
        src_dir: Source directory path

    Returns:
        The output file path for the .cj file
    """
    # Convert schema filename to path
    # e.g., commons-fileupload.src.main.org.apache.commons.fileupload.disk.DiskFileItem
    #     -> commons-fileupload/src/main/org/apache/commons/fileupload/disk/DiskFileItem
    path_parts = formatted_schema_fname.replace(".", "/").split("/")

    # Remove first part (project) and last part (class name)
    path_parts = path_parts[1:-1]
    # e.g., ['src', 'main', 'org', 'apache', 'commons', 'fileupload', 'disk']

    # Find 'main' or 'test' index to determine base directory
    base_index = -1
    for i, part in enumerate(path_parts):
        if part in ("main", "test"):
            base_index = i
            break

    # Get the subdirectory after the base (main/test) + package path (org/apache/commons/fileupload)
    # We want to keep the part after those 5 fixed segments
    if base_index >= 0:
        # Skip base (main/test) + 5 package segments (org/apache/commons/fileupload)
        # i.e., skip base_index + 5 elements
        java_sub_dir = "/".join(path_parts[base_index + 5 :])
    else:
        # No main/test found, use default logic
        java_sub_dir = "/".join(path_parts[-1:]) if len(path_parts) > 1 else ""

    # Build output path based on is_test
    if is_test:
        # Test files go to src/test/ subdirectory
        test_base = f"{src_dir}/test"
        if java_sub_dir:
            return f"{test_base}/{java_sub_dir}/{class_name}.cj"
        else:
            return f"{test_base}/{class_name}.cj"
    else:
        # Main files go to src/ directory
        if java_sub_dir:
            return f"{src_dir}/{java_sub_dir}/{class_name}.cj"
        else:
            return f"{src_dir}/{class_name}.cj"


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


def split_with_nested_commas(s):
    result = []
    stack = []
    start = 0

    for i, c in enumerate(s):
        if c == "," and not stack:
            result.append(s[start:i].strip())
            start = i + 1
        elif c == "<":
            stack.append(c)
        elif c == ">":
            stack.pop()

    result.append(s[start:].strip())
    return result


def get_dependency_path(dependent_class, project, suffix):
    """Get the dependency path for a class."""
    if dependent_class.startswith(project):
        return ".".join(dependent_class.split(".")[1:-1])
    else:
        return dependent_class.replace(".", "/")


def remove_duplicate_methods(schema):
    duplicate_methods = {}
    for class_ in schema["classes"]:
        duplicate_methods.setdefault(class_, {})
        for method in schema["classes"][class_]["methods"]:
            schema["classes"][class_]["methods"][method]["is_overload"] = False
            method_name = method.split(":")[1].strip()
            duplicate_methods[class_].setdefault(method_name, [])
            duplicate_methods[class_][method_name].append(method)

    for class_ in duplicate_methods:
        for method_name in duplicate_methods[class_]:
            if len(duplicate_methods[class_][method_name]) > 1:
                for k in duplicate_methods[class_][method_name]:
                    schema["classes"][class_]["methods"][k]["is_overload"] = True

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


def has_child_parent_dept(dependent_files, class_path, project, suffix):
    verified_dependent_files = []
    for class_1, class_2 in dependent_files:
        class_1_path = get_dependency_path(class_path[class_1], project, suffix)
        class_2_path = get_dependency_path(class_path[class_2], project, suffix)

        class_1_schema_name = (
            f"data/java/schemas{suffix}/{project}/{project}.{class_1_path}.json"
        )
        class_2_schema_name = (
            f"data/java/schemas{suffix}/{project}/{project}.{class_2_path}.json"
        )

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

    # Use global type mapping
    return cangjie_type_map.get(java_type, java_type)


def normalize_class_names(class_names, extracted_types, class_path):
    """
    Normalize class names: remove generics, apply type mapping, and clean up.

    Args:
        class_names: List of class/interface names to normalize
        extracted_types: Dictionary of extracted type mappings
        class_path: Set of class paths to skip for type mapping

    Returns:
        List of normalized class names
    """
    # Step 1: Remove generic type parameters (e.g., List<T> -> List)
    normalized = [
        cls_name.split("<")[0].replace("new ", "").strip() for cls_name in class_names
    ]
    # Step 2: Remove parentheses (for constructors)
    normalized = [
        cls_name.split("(")[0].replace("new ", "").strip() for cls_name in normalized
    ]
    # Step 3: Apply type mapping if available and not in class_path
    normalized = [
        (
            extracted_types[cls_name]
            if cls_name in extracted_types and cls_name not in class_path
            else cls_name
        )
        for cls_name in normalized
    ]
    return normalized


def main(args):

    with open(f"data/java/type_resolution/universal_type_map_final.json", "r") as f:
        extracted_types = json.load(f)

    # TODO:unprocessed
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

    schemas = os.listdir(f"data/java/schemas{args.suffix}/{args.project}")

    dependencies_dir = f"data/java/dependencies{args.suffix}"
    with open(f"{dependencies_dir}/{args.project}/dependencies.json", "r") as f:
        dependencies = json.load(f)

    dependent_files, class_path = get_dependency_cycle(dependencies)
    verified_dependent_files = has_child_parent_dept(
        dependent_files, class_path, args.project, args.suffix
    )

    for schema_fname in schemas:
        if args.suffix == "_evosuite" and not schema_fname.endswith("ESTest.json"):
            continue

        if args.suffix != "_evosuite" and "ESTest" in schema_fname:
            continue

        schema_path = f"data/java/schemas{args.suffix}/{args.project}/{schema_fname}"

        schema = {}
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # TODO: preserve method overloading
        schema = remove_duplicate_methods(schema)

        # Cangjie uses package declaration instead of imports at the top
        skeleton = "// Package Declaration\npackage "

        # Extract package name: take path parts after first 3 (skip org/apache/xxx)
        if "src/test/java" in schema["path"]:
            # For test files, use project.test as package
            package_name = f"{args.project}.test"
        elif "src/main/java" in schema["path"]:
            full_package = schema["path"].split("src/main/java/")[1].rsplit("/", 1)[0]
        elif "src" in schema["path"]:
            full_package = schema["path"].split("src/")[1].rsplit("/", 1)[0]
        else:
            full_package = args.project

        # Take parts after first 3 (skip org/apache/commons or com/example)
        # Skip if package_name was already set for test files above
        if "src/test/java" not in schema["path"]:
            package_parts = full_package.split("/")
            if len(package_parts) > 3:
                package_name = "/".join(package_parts[3:])
            else:
                package_name = args.project

        skeleton += package_name.replace("/", ".") + "\n\n"

        skeleton += "// Imports Begin\n"
        skeleton += "// Imports End\n\n"

        target_schema = schema.copy()
        cangjie_imports = []
        class_order = get_class_order(schema)

        # Process main_methods if exists (main function stored separately from classes)
        main_method_template = None
        if "main_methods" in schema:
            if "main" in schema["main_methods"]:
                main_method_template = f"main(args: Array<String>): Int64 {{\n\tthrow Exception('TODO')\n}}\n"
                # Add main_methods to target_schema, preserve original fields
                target_schema.setdefault("main_methods", {})
                target_schema["main_methods"]["main"] = {
                    "start": schema["main_methods"]["main"]["start"],
                    "end": schema["main_methods"]["main"]["end"],
                    "body": schema["main_methods"]["main"]["body"],
                    "is_constructor": schema["main_methods"]["main"]["is_constructor"],
                    "annotations": schema["main_methods"]["main"]["annotations"],
                    "modifiers": schema["main_methods"]["main"]["modifiers"],
                    "return_types": schema["main_methods"]["main"]["return_types"],
                    "signature": schema["main_methods"]["main"]["signature"],
                    "parameters": schema["main_methods"]["main"]["parameters"],
                    "calls": schema["main_methods"]["main"]["calls"],
                    "partial_translation": [
                        f"func main(args: Array<String>): Int64 {{",
                        "\tthrow Exception('TODO')",
                        "\t}\n",
                    ],
                    "translation": [],
                    "translation_status": "pending",
                    "cangjie_compilation": "pending",
                    "test_execution": {},
                    "elapsed_time": 0,
                }

        # Begin processing classes
        class_dependencies = []
        for class_ in class_order:
            if "new" in class_ or "{" in class_:  # skip nested and nameless classes
                continue

            # Read Java source code by line range to mark if class is enum
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

            # If nested class, find its top-level parent class
            main_class = class_
            if schema["classes"][class_]["nested_inside"] != []:
                main_class = schema["classes"][class_]["nested_inside"]
                dependencies.setdefault(main_class, [])
                dependencies[main_class].append(main_class)

            dependencies[main_class] += schema["classes"][main_class]["nests"]

            # Record nested class relationships
            if class_ in dependencies:
                class_dependencies.append((schema["path"], dependencies[class_]))

            # Extract class name
            class_name = class_
            if "<" in class_:
                class_name = class_.split("<")[0].replace("new ", "").strip()
            elif "(" in class_:
                class_name = class_.split("(")[0].replace("new ", "").strip()

            # Cangjie class declaration using < for inheritance
            class_declaration = ""
            # TODO: These Java interfaces should not be parent classes in translation
            # exceptional_superclasses = {
            #     "Comparator",
            #     "Queue",
            #     "Comparable",
            #     "Closeable",
            #     "Enum",
            #     "Iterator",
            #     "Iterable",
            #     "Supplier",
            #     "Runnable",
            # }

            # Determine class type markers
            is_interface = schema["classes"][class_].get("is_interface", False)
            is_abstract = schema["classes"][class_].get("is_abstract", False)

            if schema["classes"][class_]["extends"] != []:
                schema["classes"][class_]["extends"] = normalize_class_names(
                    schema["classes"][class_]["extends"], extracted_types, class_path
                )

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
                schema["classes"][class_]["implements"] = normalize_class_names(
                    schema["classes"][class_]["implements"], extracted_types, class_path
                )

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
                if "import std.unittest.*" not in cangjie_imports:
                    cangjie_imports.append("import std.unittest.*")
                if "import std.unittest.testmacro.*" not in cangjie_imports:
                    cangjie_imports.append("import std.unittest.testmacro.*")

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
                    ]["cangjie_compilation"] = "pending"
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["test_execution"] = {}
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["elapsed_time"] = 0
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["generation_timestamp"] = 0
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["model"] = (
                        args.model if args.model else "deepseek-coder-33b-instruct"
                    )
                    target_schema["classes"][class_]["static_initializers"][
                        static_initializer_se
                    ]["include_implementation"] = (
                        True if args.type == "body" else False
                    )

            # Process fields
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
                    # TODO: elif field_type == cla_name:
                    else:
                        field_body = "?"
                # Process List type fields
                elif "=" in "".join(schema["classes"][class_]["fields"][field]["body"]):
                    if "new ArrayList" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ) or "new LinkedList" in "".join(
                        schema["classes"][class_]["fields"][field]["body"]
                    ):
                        field_body = "[]"
                    elif (
                        "new LinkedHashMap"
                        in "".join(schema["classes"][class_]["fields"][field]["body"])
                        or "new HashMap"
                        in "".join(schema["classes"][class_]["fields"][field]["body"])
                        or "new EnumMap"
                        in "".join(schema["classes"][class_]["fields"][field]["body"])
                    ):
                        field_body = "[:]"
                    else:
                        field_body = "?"

                # Save field info to target_schema
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
                    "cangjie_compilation"
                ] = "pending"
                target_schema["classes"][class_]["fields"][field][
                    "test_execution"
                ] = {}
                target_schema["classes"][class_]["fields"][field]["elapsed_time"] = 0
                target_schema["classes"][class_]["fields"][field][
                    "generation_timestamp"
                ] = 0
                target_schema["classes"][class_]["fields"][field]["model"] = (
                    args.model if args.model else "deepseek-coder-33b-instruct"
                )
                target_schema["classes"][class_]["fields"][field][
                    "include_implementation"
                ] = (True if args.type == "body" else False)

                skeleton += f"\t{access_modifier}{var_keyword}{field_name}: {field_type} = {field_body}\n"

            skeleton += "\t// Class Fields End\n\n"

            skeleton += "\t// Class Methods Begin\n"
            # For Cangjie, main function needs to be outside the class
            # Only reset if main_methods wasn't detected at file level
            if "main_methods" not in schema:
                main_method_template = None
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

                # Special handling for main function - Cangjie main doesn't use func keyword
                is_main = method_name == "main"

                # Check if this is a constructor (method name equals class name)
                is_constructor = class_ == method_name

                # Get return type
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
                        skeleton += f"\t{access_modifier}init() {{\n\t\tthrow Exception('TODO')\n\t}}\n"
                        current_method.append(f"\t{access_modifier}init() {{")
                    elif is_main and "main_methods" not in schema:
                        # Special handling for main function - save for later (outside class)
                        main_method_template = f"main(args: Array<String>): Int64 {{\n\tthrow Exception('TODO')\n}}\n"
                        # Create partial_translation for main method before skipping
                        target_schema["classes"][class_]["methods"][method][
                            "partial_translation"
                        ] = [
                            f"\tpublic func {method_name}(args: Array<String>): Int64 {{",
                            "\t\tthrow Exception('TODO')",
                            "\t}\n",
                        ]
                        target_schema["classes"][class_]["methods"][method][
                            "translation"
                        ] = []
                        target_schema["classes"][class_]["methods"][method][
                            "translation_status"
                        ] = "pending"
                        target_schema["classes"][class_]["methods"][method][
                            "cangjie_compilation"
                        ] = "pending"
                        target_schema["classes"][class_]["methods"][method][
                            "test_execution"
                        ] = {}
                        target_schema["classes"][class_]["methods"][method][
                            "elapsed_time"
                        ] = 0
                        target_schema["classes"][class_]["methods"][method][
                            "generation_timestamp"
                        ] = 0
                        target_schema["classes"][class_]["methods"][method]["model"] = (
                            args.model if args.model else "deepseek-coder-33b-instruct"
                        )
                        target_schema["classes"][class_]["methods"][method][
                            "include_implementation"
                        ] = (True if args.type == "body" else False)
                        continue  # Skip adding to class
                    else:
                        if is_static:
                            skeleton += f"\t{access_modifier}{static_prefix}func {method_name}(): {return_type} {{\n\t\tthrow Exception('TODO')\n\t}}\n"
                            current_method.append(
                                f"\t{access_modifier}{static_prefix}func {method_name}(): {return_type} {{"
                            )
                        else:
                            skeleton += f"\t{access_modifier}func {method_name}(): {return_type} {{\n\t\tthrow Exception('TODO')\n\t}}\n"
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
                            + ") {\n\t\tthrow Exception('TODO')\n\t}\n"
                        )
                        current_method.append(
                            f"\t{access_modifier}init("
                            + ", ".join([x + f": {y.strip()}" for x, y in param_types])
                            + ") {"
                        )
                    elif is_main and "main_methods" not in schema:
                        # Special handling for main function - always use Array<String>
                        main_method_template = f"main(args: Array<String>): Int64 {{\n\tthrow Exception('TODO')\n}}\n"
                        # Create partial_translation for main method before skipping
                        target_schema["classes"][class_]["methods"][method][
                            "partial_translation"
                        ] = [
                            f"\tpublic func {method_name}(args: Array<String>): Int64 {{",
                            "\t\tthrow Exception('TODO')",
                            "\t}\n",
                        ]
                        target_schema["classes"][class_]["methods"][method][
                            "translation"
                        ] = []
                        target_schema["classes"][class_]["methods"][method][
                            "translation_status"
                        ] = "pending"
                        target_schema["classes"][class_]["methods"][method][
                            "cangjie_compilation"
                        ] = "pending"
                        target_schema["classes"][class_]["methods"][method][
                            "test_execution"
                        ] = {}
                        target_schema["classes"][class_]["methods"][method][
                            "elapsed_time"
                        ] = 0
                        target_schema["classes"][class_]["methods"][method][
                            "generation_timestamp"
                        ] = 0
                        target_schema["classes"][class_]["methods"][method]["model"] = (
                            args.model if args.model else "deepseek-coder-33b-instruct"
                        )
                        target_schema["classes"][class_]["methods"][method][
                            "include_implementation"
                        ] = (True if args.type == "body" else False)
                        continue  # Skip adding to class
                    else:
                        if is_static:
                            skeleton += (
                                f"\t{access_modifier}{static_prefix}func {method_name}("
                                + ", ".join(
                                    [x + f": {y.strip()}" for x, y in param_types]
                                )
                                + f"): {return_type} {{\n\t\tthrow Exception('TODO')\n\t}}\n"
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
                                + f"): {return_type} {{\n\t\tthrow Exception('TODO')\n\t}}\n"
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

                current_method.append("\t\tthrow Exception('TODO')")
                current_method.append("\t}\n")

                target_schema["classes"][class_]["methods"][method][
                    "partial_translation"
                ] = current_method
                target_schema["classes"][class_]["methods"][method]["translation"] = []
                target_schema["classes"][class_]["methods"][method][
                    "translation_status"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "cangjie_compilation"
                ] = "pending"
                target_schema["classes"][class_]["methods"][method][
                    "test_execution"
                ] = {}
                target_schema["classes"][class_]["methods"][method]["elapsed_time"] = 0
                target_schema["classes"][class_]["methods"][method][
                    "generation_timestamp"
                ] = 0
                target_schema["classes"][class_]["methods"][method]["model"] = (
                    args.model if args.model else "deepseek-coder-33b-instruct"
                )
                target_schema["classes"][class_]["methods"][method][
                    "include_implementation"
                ] = (True if args.type == "body" else False)

            skeleton += "\t// Class Methods End\n\n"
            skeleton += "}\n\n"

            # Add main function outside the class if exists, otherwise add dummy main
            if main_method_template:
                skeleton += main_method_template + "\n"
            else:
                skeleton += "main(args: Array<String>): Int64 {\n    // dummy main (original source doesn't have main)\n    0\n}\n"

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
                    dependent_class[1], args.project, args.suffix
                )
                # If two classes already have inheritance (parent-child), no separate import needed
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

                # Remove company name and project name from import path
                # e.g., import org.apache.commons.fileupload.ProgressListener -> import ProgressListener
                # e.g., import org.apache.commons.fileupload.disk.DiskFileItem -> import disk.DiskFileItem
                full_import_path = path.replace("/", ".")

                # Special handling for commons-fileupload project
                if args.project == "commons-fileupload":
                    # Remove "org.apache.commons.fileupload" prefix
                    if full_import_path.startswith("org.apache.commons.fileupload."):
                        import_path = full_import_path[
                            len("org.apache.commons.fileupload.") :
                        ]
                    else:
                        import_path = full_import_path
                else:
                    # Default: remove "org.apache.{project}" prefix
                    import_parts = full_import_path.split(".")
                    if (
                        len(import_parts) >= 3
                        and import_parts[0] == "org"
                        and import_parts[1] == "apache"
                    ):
                        import_path = ".".join(import_parts[3:])
                    elif (
                        len(import_parts) >= 3
                        and import_parts[0] == "com"
                        and import_parts[1] == "example"
                    ):
                        # For com.example.xxx projects, use project name as package
                        # e.g., com.example.helloworld.HelloWorld -> HelloWorld.HelloWorld
                        class_name = import_parts[-1]
                        import_path = f"{args.project}.{class_name}"
                    else:
                        import_path = full_import_path

                import_stmt = f"import {import_path}"
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
                    "joda.convert" in current_line and args.project == "joda-money"
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

        project_dir = f"data/java/skeletons/{args.project}"
        src_dir = f"{project_dir}/src"

        # Create project directories first
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(src_dir, exist_ok=True)

        # Create cjpm.toml file if it doesn't exist
        cjpm_toml_path = f"{project_dir}/cjpm.toml"
        if not os.path.exists(cjpm_toml_path):
            cjpm_toml_content = f"""[package]
name = "{args.project}"
version = "0.1.0"

[dependencies]
"""
            with open(cjpm_toml_path, "w") as f:
                f.write(cjpm_toml_content)

        formatted_schema_fname = ".".join(schema_fname.split(".")[:-1])
        class_name = formatted_schema_fname.split(".")[-1]

        # Determine if this is a test file
        is_test = "Test" in schema_fname or args.suffix == "_evosuite"

        # Calculate output file path
        file_path = calculate_output_path(
            formatted_schema_fname=formatted_schema_fname,
            class_name=class_name,
            project=args.project,
            is_test=is_test,
            src_dir=src_dir,
        )

        # Create directory if needed
        file_dir = os.path.dirname(file_path)
        os.makedirs(file_dir, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(skeleton)

        # translations - 保持与 data/java/skeletons/<project> 相同的目录结构
        # 从 file_path 中提取相对于 project_dir 的路径部分
        relative_path = os.path.relpath(file_path, project_dir)
        translations_skeleton_dir = f"data/java/skeletons/translations/{args.model}/{args.type}/{args.temperature}/{args.project}"
        os.makedirs(translations_skeleton_dir, exist_ok=True)
        translations_file_path = os.path.join(translations_skeleton_dir, relative_path)
        os.makedirs(os.path.dirname(translations_file_path), exist_ok=True)
        with open(translations_file_path, "w") as f:
            f.write(skeleton)

        os.makedirs(
            f"data/java/schemas{args.suffix}/translations/{args.model}/{args.type}/{args.temperature}/{args.project}",
            exist_ok=True,
        )
        with open(
            f"data/java/schemas{args.suffix}/translations/{args.model}/{args.type}/{args.temperature}/{args.project}/{formatted_schema_fname}_cangjie_partial.json",
            "w",
        ) as f:
            json.dump(target_schema, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Cangjie class skeleton")
    parser.add_argument(
        "--project", type=str, dest="project", help="name of the project"
    )
    parser.add_argument("--model", type=str, dest="model", help="name of the model")
    parser.add_argument(
        "--type", type=str, dest="type", help="prompt type signature/body"
    )
    parser.add_argument("--suffix", type=str, dest="suffix", help="suffix")
    parser.add_argument(
        "--temperature", type=float, dest="temperature", help="temperature"
    )
    args = parser.parse_args()

    main(args)
