import os
import json
import argparse
from utils import (
    parse_location,
    parse_location_with_end,
    parse_location_simple,
    read_file_lines,
    find_callable_body,
    expand_callable_body,
)


def process_imports(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process imports query and populate schemas."""
    imports_query_out = f"{query_outputs_dir}/{project}/{project}_imports.txt"
    with open(imports_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        import_name, start = [x.strip() for x in res_row]

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        schemas.setdefault(path, {})

        import_body = read_file_lines(path, start_line, end_line)

        schemas[path].setdefault("path", path)
        schemas[path].setdefault("imports", {})
        schemas[path].setdefault("classes", {})
        schemas[path]["imports"].setdefault(
            f"{start_line}-{end_line}:{import_name}",
            {
                "start": start_line,
                "end": end_line,
                "body": import_body,
            },
        )


def process_callables(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process class callables (methods) query and populate schemas."""
    callables_query_out = f"{query_outputs_dir}/{project}/{project}_class_callables.txt"
    with open(callables_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        (
            class_name,
            class_location,
            callable_name,
            modifier,
            return_type,
            return_type_qualified_name,
            signature,
            annotation_location,
            start,
            end,
        ) = [x.strip() for x in res_row]

        if callable_name in ["<clinit>", "<obinit>"]:
            continue

        assert "<clinit>" not in callable_name and "<obinit>" not in callable_name

        if start.endswith("0:0:0:0") or end.endswith("0:0:0:0"):
            continue

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        schemas.setdefault(path, {})

        # Adjust to 0-based for internal use
        start_line = start_line - 1

        class_location_path, class_start_line, class_end_line = parse_location_with_end(class_location)

        if "new" not in class_name and "{" not in class_name:
            class_declaration = read_file_lines(path, class_start_line, class_end_line)

            if class_start_line == class_end_line:
                changed = False
                while "{" not in "".join(class_declaration):
                    class_declaration = read_file_lines(path, class_start_line, class_end_line)
                    class_end_line += 1
                    changed = True

                if changed:
                    class_end_line -= 1

        # Use find_callable_body to adjust start line
        callable_body, start_line = find_callable_body(path, start_line, end_line)

        if start == end:
            callable_body, start_line, end_line = expand_callable_body(path, start_line, end_line)

        schemas[path].setdefault("path", path)
        schemas[path].setdefault("imports", {})
        schemas[path].setdefault("classes", {})
        schemas[path]["classes"].setdefault(class_name, {})
        schemas[path]["classes"][class_name].setdefault("start", class_start_line)
        schemas[path]["classes"][class_name].setdefault("end", class_end_line)
        schemas[path]["classes"][class_name].setdefault("is_abstract", False)
        schemas[path]["classes"][class_name].setdefault("is_interface", False)
        schemas[path]["classes"][class_name].setdefault("nested_inside", [])
        schemas[path]["classes"][class_name].setdefault("nests", [])
        schemas[path]["classes"][class_name].setdefault("implements", [])
        schemas[path]["classes"][class_name].setdefault("extends", [])
        pos_callable_name = f"{start_line}-{end_line}:{callable_name}"
        schemas[path]["classes"][class_name].setdefault("methods", {})

        if "public class" in "".join(callable_body) or "public static class" in "".join(
            callable_body
        ):
            continue

        already_exists = False
        for method in schemas[path]["classes"][class_name]["methods"].keys():
            if (
                callable_name in method
                and start_line
                == schemas[path]["classes"][class_name]["methods"][method]["start"]
                and end_line
                != schemas[path]["classes"][class_name]["methods"][method]["end"]
            ):
                already_exists = True
                break

        if already_exists:
            continue

        schemas[path]["classes"][class_name]["methods"].setdefault(
            pos_callable_name,
            {
                "start": start_line,
                "end": end_line,
                "body": callable_body,
                "is_constructor": False,
                "annotations": [],
                "modifiers": [],
                "return_types": [],
                "signature": signature,
                "parameters": [],
                "calls": [],
            },
        )

        return_type_qualified = _parse_return_type(return_type, return_type_qualified_name)

        if (return_type, return_type_qualified) not in schemas[path]["classes"][
            class_name
        ]["methods"][pos_callable_name]["return_types"]:
            schemas[path]["classes"][class_name]["methods"][pos_callable_name][
                "return_types"
            ].append((return_type, return_type_qualified))

        if (
            modifier
            not in schemas[path]["classes"][class_name]["methods"][pos_callable_name][
                "modifiers"
            ]
            and modifier != "null"
        ):
            schemas[path]["classes"][class_name]["methods"][pos_callable_name][
                "modifiers"
            ].append(modifier)

        if callable_name == class_name:
            schemas[path]["classes"][class_name]["methods"][pos_callable_name][
                "is_constructor"
            ] = True

        _process_annotation(schemas, path, class_name, pos_callable_name, annotation_location)


def process_interfaces(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process interfaces query and populate schemas."""
    interfaces_query_out = f"{query_outputs_dir}/{project}/{project}_interfaces.txt"
    with open(interfaces_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        (
            interface_name,
            interface_loc,
            callable_name,
            modifier,
            return_type,
            return_type_qualified_name,
            siganture,
            start,
            end,
        ) = [x.strip() for x in res_row]

        if callable_name in ["<clinit>", "<obinit>"]:
            continue

        if (
            callable_name == "null"
            and modifier == "null"
            and return_type == "null"
            and return_type_qualified_name == "null"
            and siganture == "null"
        ):
            _add_interface_declaration(schemas, projects_dir, project, interface_loc, interface_name)
            continue

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        schemas.setdefault(path, {})

        # Adjust to 0-based for internal use
        start_line = start_line - 1

        interface_start_line, interface_end_line = parse_location_with_end(interface_loc)[1:3]

        # Use find_callable_body to adjust start line
        callable_body, start_line = find_callable_body(path, start_line, end_line)

        if start == end:
            callable_body, start_line, end_line = expand_callable_body(path, start_line, end_line)

        schemas[path].setdefault("path", path)
        schemas[path].setdefault("imports", {})
        schemas[path].setdefault("classes", {})
        schemas[path]["classes"].setdefault(interface_name, {})
        schemas[path]["classes"][interface_name].setdefault(
            "start", interface_start_line
        )
        schemas[path]["classes"][interface_name].setdefault("end", interface_end_line)
        schemas[path]["classes"][interface_name].setdefault("is_abstract", False)
        schemas[path]["classes"][interface_name].setdefault("is_interface", True)
        schemas[path]["classes"][interface_name].setdefault("nested_inside", [])
        schemas[path]["classes"][interface_name].setdefault("nests", [])
        schemas[path]["classes"][interface_name].setdefault("implements", [])
        schemas[path]["classes"][interface_name].setdefault("extends", [])
        pos_callable_name = f"{start_line}-{end_line}:{callable_name}"
        schemas[path]["classes"][interface_name].setdefault("methods", {})
        schemas[path]["classes"][interface_name]["methods"].setdefault(
            pos_callable_name,
            {
                "start": start_line,
                "end": end_line,
                "body": callable_body,
                "is_constructor": False,
                "annotations": [],
                "modifiers": [],
                "return_types": [],
                "signature": siganture,
                "parameters": [],
                "calls": [],
            },
        )

        return_type_qualified = _parse_return_type(return_type, return_type_qualified_name)

        if (return_type, return_type_qualified) not in schemas[path]["classes"][
            interface_name
        ]["methods"][pos_callable_name]["return_types"]:
            schemas[path]["classes"][interface_name]["methods"][pos_callable_name][
                "return_types"
            ].append((return_type, return_type_qualified))

        if (
            modifier
            not in schemas[path]["classes"][interface_name]["methods"][
                pos_callable_name
            ]["modifiers"]
        ):
            schemas[path]["classes"][interface_name]["methods"][pos_callable_name][
                "modifiers"
            ].append(modifier)

        if callable_name == interface_name:
            schemas[path]["classes"][interface_name]["methods"][pos_callable_name][
                "is_constructor"
            ] = True


def process_fields(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process fields query and populate schemas."""
    # Initialize fields for all classes
    for path in schemas.keys():
        for class_ in schemas[path]["classes"].keys():
            schemas[path]["classes"][class_].setdefault("fields", {})

    fields_query_out = f"{query_outputs_dir}/{project}/{project}_fields.txt"
    with open(fields_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        (
            field_name,
            modifier,
            return_type,
            return_type_qualified_name,
            start,
            class_name,
        ) = [x.strip() for x in res_row]

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        schemas.setdefault(path, {})

        field_body = read_file_lines(path, start_line, end_line)

        schemas[path]["classes"][class_name].setdefault("fields", {})
        schemas[path]["classes"][class_name]["fields"].setdefault(
            f"{start_line}-{end_line}:{field_name}",
            {
                "start": start_line,
                "end": end_line,
                "body": field_body,
                "modifiers": [],
                "types": [],
            },
        )
        return_type_qualified = _parse_return_type(return_type, return_type_qualified_name)

        if (return_type, return_type_qualified) not in schemas[path]["classes"][
            class_name
        ]["fields"][f"{start_line}-{end_line}:{field_name}"]["types"]:
            schemas[path]["classes"][class_name]["fields"][
                f"{start_line}-{end_line}:{field_name}"
            ]["types"].append((return_type, return_type_qualified))

        if (
            modifier
            not in schemas[path]["classes"][class_name]["fields"][
                f"{start_line}-{end_line}:{field_name}"
            ]["modifiers"]
            and modifier != "null"
        ):
            schemas[path]["classes"][class_name]["fields"][
                f"{start_line}-{end_line}:{field_name}"
            ]["modifiers"].append(modifier)


def process_superclasses(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process superclasses query and populate schemas."""
    classes_query_out = f"{query_outputs_dir}/{project}/{project}_superclasses.txt"
    with open(classes_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        class_name, is_abstract, parent_class, start = [x.strip() for x in res_row]

        path = parse_location_simple(start)[0]
        path = projects_dir + path[path.find(project) :]

        if path.endswith(".class") or "new" in class_name or "{" in class_name:
            continue

        schemas[path]["classes"][class_name]["is_abstract"] = (
            True if is_abstract == "true" else False
        )

        if parent_class == "Object":
            continue

        class_start_line = schemas[path]["classes"][class_name]["start"]
        class_end_line = schemas[path]["classes"][class_name]["end"]

        file_lines = read_file_lines(path, class_start_line, class_end_line)
        class_declaration = file_lines[0].split("{")[0]

        if "extends" in class_declaration:
            schemas[path]["classes"][class_name]["extends"].append(parent_class)
        elif "implements" in class_declaration:
            schemas[path]["classes"][class_name]["implements"].append(parent_class)


def process_static_initializers(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process static initializers query and populate schemas."""
    static_initializers_query_out = (
        f"{query_outputs_dir}/{project}/{project}_static_initializers.txt"
    )
    with open(static_initializers_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        class_name, start = [x.strip() for x in res_row]

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        static_initializer_body = read_file_lines(path, start_line, end_line)

        schemas[path]["classes"][class_name].setdefault("static_initializers", {})
        schemas[path]["classes"][class_name]["static_initializers"].setdefault(
            f"{start_line}-{end_line}:run_static_init",
            {"start": start_line, "end": end_line, "body": static_initializer_body},
        )


def process_nested_classes(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process nested classes query and populate schemas."""
    nested_classes_query_out = (
        f"{query_outputs_dir}/{project}/{project}_nested_classes.txt"
    )
    with open(nested_classes_query_out, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        class_name, start, nested_inside = [x.strip() for x in res_row]

        path = parse_location_simple(start)[0]
        path = projects_dir + path[path.find(project) :]

        schemas[path]["classes"][class_name]["nested_inside"] = nested_inside
        schemas[path]["classes"][nested_inside]["nests"].append(class_name)


def process_parameters(schemas: dict, projects_dir: str, query_outputs_dir: str, project: str):
    """Process parameters query and populate schemas."""
    parameters = f"{query_outputs_dir}/{project}/{project}_parameters.txt"
    with open(parameters, "r") as f:
        lines = f.readlines()

    for line in lines:
        res_row = line.split("|")[1:-1]
        class_name, method_name, parameter_name, start, end = [
            x.strip() for x in res_row
        ]

        path, start_line, end_line = parse_location_with_end(start)
        path = projects_dir + path[path.find(project) :]

        # Adjust to 0-based for internal use
        start_line = start_line - 1

        # Use find_callable_body to adjust start line
        callable_body, start_line = find_callable_body(path, start_line, end_line)

        if start == end:
            callable_body, start_line, end_line = expand_callable_body(path, start_line, end_line)

        schemas[path]["classes"][class_name]["methods"][
            f"{start_line}-{end_line}:{method_name}"
        ]["parameters"].append(parameter_name)


def _parse_return_type(return_type: str, return_type_qualified_name: str) -> str:
    """Parse return type from qualified name."""
    if "java" in return_type_qualified_name:
        temp_name = (
            return_type_qualified_name[return_type_qualified_name.find("java") :]
            .replace("/", ".")
            .replace(";", "")
        )
        return ".".join(temp_name.split(".")[:-1]) + "." + return_type
    else:
        return return_type


def _add_interface_declaration(schemas: dict, projects_dir: str, project: str,
                                  interface_loc: str, interface_name: str):
    """Add interface declaration to schemas."""
    path, interface_start_line, interface_end_line = parse_location_with_end(interface_loc)
    path = projects_dir + path[path.find(project) :]
    schemas.setdefault(path, {})
    schemas[path].setdefault("path", path)
    schemas[path].setdefault("imports", {})
    schemas[path].setdefault("classes", {})
    schemas[path]["classes"].setdefault(interface_name, {})
    schemas[path]["classes"][interface_name].setdefault(
        "start", interface_start_line
    )
    schemas[path]["classes"][interface_name].setdefault(
        "end", interface_end_line
    )
    schemas[path]["classes"][interface_name].setdefault("is_abstract", False)
    schemas[path]["classes"][interface_name].setdefault("is_interface", True)
    schemas[path]["classes"][interface_name].setdefault("nested_inside", [])
    schemas[path]["classes"][interface_name].setdefault("nests", [])
    schemas[path]["classes"][interface_name].setdefault("implements", [])
    schemas[path]["classes"][interface_name].setdefault("extends", [])
    schemas[path]["classes"][interface_name].setdefault("methods", {})


def _process_annotation(schemas: dict, path: str, class_name: str,
                        pos_callable_name: str, annotation_location: str):
    """Process annotation for a method."""
    if annotation_location != "null":
        annotation_path, annotation_start_line, annotation_start_col, annotation_end_line, annotation_end_col = parse_location(annotation_location)
        annotation_body_lines = read_file_lines(annotation_path, annotation_start_line, annotation_end_line)
        if annotation_body_lines:
            annotation_body = annotation_body_lines[0][annotation_start_col:annotation_end_col]
            schemas[path]["classes"][class_name]["methods"][pos_callable_name][
                "annotations"
            ].append(annotation_body)


def _remove_constructor_methods(schemas: dict):
    """Remove constructor methods that match class declaration."""
    for path in schemas.copy().keys():
        for class_ in schemas[path]["classes"].copy().keys():
            for method_ in schemas[path]["classes"][class_]["methods"].copy().keys():
                if schemas[path]["classes"][class_]["methods"][method_][
                    "is_constructor"
                ]:
                    if (
                        method_
                        == f'{schemas[path]["classes"][class_]["start"]}-{schemas[path]["classes"][class_]["end"]}:{class_}'
                    ):
                        schemas[path]["classes"][class_]["methods"].pop(method_)


def _save_schemas(schemas: dict, project: str, suffix: str):
    """Save schemas to JSON files."""
    for k, v in schemas.items():
        key = k[k.find(project) :].replace("/", ".")
        if suffix == "_evosuite" and "ESTest" not in key:
            continue
        key = key.replace(".java", "")
        with open(f"data/java/schemas{suffix}/{project}/{key}.json", "w") as f:
            json.dump(v, f, indent=4)


def create_schema(args):
    """Main function to create schema for the project."""
    project = args.project
    projects_dir = f"projects/java/cleaned_final_projects{args.suffix}/"
    query_outputs_dir = f"data/java/query_outputs{args.suffix}"
    os.makedirs(f"data/java/schemas{args.suffix}/{project}", exist_ok=True)
    schemas = {}

    # Process each query type
    process_imports(schemas, projects_dir, query_outputs_dir, project)
    process_callables(schemas, projects_dir, query_outputs_dir, project)
    process_interfaces(schemas, projects_dir, query_outputs_dir, project)
    process_fields(schemas, projects_dir, query_outputs_dir, project)
    process_superclasses(schemas, projects_dir, query_outputs_dir, project)
    process_static_initializers(schemas, projects_dir, query_outputs_dir, project)
    process_nested_classes(schemas, projects_dir, query_outputs_dir, project)
    process_parameters(schemas, projects_dir, query_outputs_dir, project)

    # Post-processing
    _remove_constructor_methods(schemas)

    # Save schemas
    _save_schemas(schemas, project, args.suffix)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create schema for the project")
    parser.add_argument("--project", type=str, help="Name of the project")
    parser.add_argument("--suffix", type=str, help="suffix")
    args = parser.parse_args()
    create_schema(args)
