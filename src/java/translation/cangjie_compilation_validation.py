import json
import os
import re
import subprocess

# Status constants for compilation validation
ERROR = "error"
SUCCESS = "success"
FAILURE = "failure"
NOT_EXERCISED = "not-exercised"


def get_skeleton_path(fragment: dict, args) -> str:
    """
    Build the skeleton file path based on fragment and args.

    Args:
        fragment: Fragment metadata containing schema_name, class_name, fragment_name, is_test_method
        args: Command line arguments with model, prompt_type, temperature, project

    Returns:
        str: Path to the skeleton file
    """
    # Build skeleton directory path (absolute path)
    # Structure: data/java/skeletons/translations/{model}/{prompt_type}/{temperature}/{project}/src/
    skeleton_base = os.path.abspath(f"data/java/skeletons/translations/{args.model}/{args.prompt_type}/{args.temperature}/{args.project}")
    print(f"[DEBUG] skeleton_base: {skeleton_base}", flush=True)

    # Determine if this is a test file
    if fragment.get("is_test_method"):
        # Test files are in src/test/ directory
        skeleton_dir = os.path.join(skeleton_base, "src", "test")
    else:
        skeleton_dir = os.path.join(skeleton_base, "src")

    print(f"[DEBUG] skeleton_dir: {skeleton_dir}", flush=True)

    # Build class name - for main methods, use the schema_name or "main"
    class_name = fragment.get("class_name", "")

    # For main methods (outside class), class_name is "main"
    if class_name == "main":
        # Main function is typically in a file named after the project
        skeleton_file = os.path.join(skeleton_dir, f"{args.project}.cj")
    else:
        # Regular classes: {ClassName}.cj or {ClassName}Test.cj for tests
        skeleton_file = os.path.join(skeleton_dir, f"{class_name}.cj")

    print(f"[DEBUG] skeleton_file: {skeleton_file}", flush=True)
    return skeleton_file


def find_method_in_skeleton(skeleton_content: str, fragment: dict) -> tuple:
    """
    Find the method location in skeleton content.

    Args:
        skeleton_content: The skeleton file content
        fragment: Fragment metadata with fragment_name and is_test_method

    Returns:
        tuple: (method_signature, start_pos, end_pos) or (None, None, None) if not found
    """
    fragment_name = fragment.get("fragment_name", "")
    is_test = fragment.get("is_test_method", False)
    class_name = fragment.get("class_name", "")

    # Extract actual method name - fragment_name might contain line number prefix like "8-11:testMain"
    if ":" in fragment_name:
        method_name = fragment_name.split(":")[-1]
    else:
        method_name = fragment_name

    print(f"[DEBUG] find_method_in_skeleton: fragment_name={fragment_name}, method_name={method_name}, is_test={is_test}, class_name={class_name}", flush=True)

    # For main method (function outside class) - class_name is "main" for top-level functions
    if class_name == "main":
        print(f"[DEBUG] Searching for main function pattern (class_name is main)", flush=True)
        # Look for main function pattern - multiline aware
        patterns = [
            rf"^main\s*\([^)]*\)\s*:\s*[^\{{]*\s*\{{[\s\S]*?throw Exception\('TODO'\)[\s\S]*?\}}",
            rf"^main\s*\([^)]*\)\s*:\s*[^\{{]*\{{[\s\S]*?\}}",
        ]
        for pattern in patterns:
            match = re.search(pattern, skeleton_content, re.MULTILINE | re.DOTALL)
            if match:
                print(f"[DEBUG] Main function pattern matched", flush=True)
                return ("main", match.start(), match.end())
        print(f"[DEBUG] No main function pattern matched", flush=True)
        return (None, None, None)

    # For class methods (test methods or regular methods)
    # Look for the method signature followed by throw Exception('TODO')
    # Using [\s\S] to match any character including newlines
    if is_test:
        # Test method pattern - look for @Test decorator followed by func methodName
        pattern = rf"(@Test\s+)?(public\s+|private\s+|protected\s+)?func\s+{re.escape(method_name)}\s*\([^)]*\)\s*:\s*[^\{{]*\{{[\s\S]*?throw Exception\('TODO'\)[\s\S]*?\}}"
        print(f"[DEBUG] Searching for test method pattern: {pattern}", flush=True)
    else:
        # Regular method pattern
        pattern = rf"(public\s+|private\s+|protected\s+)?func\s+{re.escape(method_name)}\s*\([^)]*\)\s*:\s*[^\{{]*\{{[\s\S]*?throw Exception\('TODO'\)[\s\S]*?\}}"
        print(f"[DEBUG] Searching for regular method pattern: {pattern}", flush=True)

    match = re.search(pattern, skeleton_content, re.MULTILINE | re.DOTALL)
    if match:
        print(f"[DEBUG] Method pattern matched at position {match.start()}-{match.end()}", flush=True)
        # Extract just the method signature part
        sig_match = re.match(rf"(?:@Test\s+)?(?:public\s+|private\s+|protected\s+)?func\s+{re.escape(method_name)}\s*\([^)]*\)\s*:\s*[^\{{]*", match.group())
        if sig_match:
            sig = sig_match.group().strip()
            print(f"[DEBUG] Extracted signature: {sig}", flush=True)
            return (sig, match.start(), match.end())

    print(f"[DEBUG] No method pattern matched", flush=True)
    return (None, None, None)


def replace_method_in_skeleton(skeleton_content: str, method_sig: str, method_body: str) -> str:
    """
    Replace throw Exception('TODO') in skeleton with new implementation.

    Args:
        skeleton_content: The skeleton file content
        method_sig: Method signature (e.g., "public func testMain(): Unit")
        method_body: New method body content

    Returns:
        str: Modified skeleton content
    """
    print(f"[DEBUG] replace_method_in_skeleton called with method_sig: {method_sig}", flush=True)
    print(f"[DEBUG] method_body: {repr(method_body[:100])}...", flush=True)

    # Find the method signature
    sig_start = skeleton_content.find(method_sig)
    if sig_start == -1:
        print(f"[DEBUG] Method signature not found", flush=True)
        return skeleton_content
    print(f"[DEBUG] sig_start: {sig_start}, content: {repr(skeleton_content[sig_start:sig_start+50])}", flush=True)

    # Find the { after the method signature
    brace_start = skeleton_content.find('{', sig_start)
    if brace_start == -1:
        print(f"[DEBUG] Opening brace not found", flush=True)
        return skeleton_content
    print(f"[DEBUG] brace_start: {brace_start}, char: {repr(skeleton_content[brace_start])}", flush=True)

    # Find the throw line after the brace
    throw_start = skeleton_content.find("throw Exception('TODO')", brace_start)
    if throw_start == -1:
        print(f"[DEBUG] throw line not found", flush=True)
        return skeleton_content
    print(f"[DEBUG] throw_start: {throw_start}", flush=True)

    # Calculate throw_indent
    line_start = skeleton_content.rfind('\n', 0, throw_start) + 1
    throw_indent = skeleton_content[line_start:throw_start]
    print(f"[DEBUG] throw_indent: '{repr(throw_indent)}', length: {len(throw_indent)}", flush=True)

    # Find the closing brace using stack-based brace matching
    close_brace_pos = -1
    brace_stack = []
    for i in range(brace_start, len(skeleton_content)):
        char = skeleton_content[i]
        if char == '{':
            brace_stack.append(i)
            print(f"[DEBUG]   Found {{ at {i}, stack: {len(brace_stack)}", flush=True)
        elif char == '}':
            if brace_stack:
                brace_stack.pop()
                print(f"[DEBUG]   Found }} at {i}, stack after pop: {len(brace_stack)}", flush=True)
                if len(brace_stack) == 0:
                    close_brace_pos = i
                    print(f"[DEBUG]   Found matching close brace at {i}", flush=True)
                    break
            else:
                print(f"[DEBUG]   Found }} at {i} but stack is empty!", flush=True)

    if close_brace_pos == -1:
        print(f"[DEBUG] Closing brace not found, final stack: {brace_stack}", flush=True)
        return skeleton_content

    print(f"[DEBUG] close_brace_pos: {close_brace_pos}", flush=True)

    # Get indentation for closing brace - find the line containing close_brace_pos
    close_brace_line_start = skeleton_content.rfind('\n', 0, close_brace_pos) + 1
    close_brace_indent = skeleton_content[close_brace_line_start:close_brace_pos]
    print(f"[DEBUG] close_brace_indent: '{repr(close_brace_indent)}'", flush=True)

    # Get indentation for method declaration line (the line with {)
    method_line_start = skeleton_content.rfind('\n', 0, brace_start) + 1
    method_indent = skeleton_content[method_line_start:brace_start]
    print(f"[DEBUG] method_indent: '{repr(method_indent)}'", flush=True)

    # Build new body - strip whitespace and add proper indentation
    # Method body content should be indented one level (one tab) more than throw_indent
    body_lines = method_body.strip().split('\n')
    new_body_lines = []
    for line in body_lines:
        stripped = line.strip()
        if stripped:
            # Use throw_indent for method body content (same level as throw statement)
            new_body_lines.append(f"{throw_indent}{stripped}")
        else:
            new_body_lines.append(f"{throw_indent}")

    new_content = '\n'.join(new_body_lines)
    print(f"[DEBUG] new_content preview: {repr(new_content[:100])}...", flush=True)

    # Build the replacement: new body followed by closing brace with correct indentation
    final_replacement = f"{new_content}\n{close_brace_indent}}}"

    # Replace throw line and closing brace with new content
    result = skeleton_content[:throw_start] + final_replacement + skeleton_content[close_brace_pos + 1:]

    print(f"[DEBUG] replace_method_in_skeleton: original length={len(skeleton_content)}, new length={len(result)}", flush=True)
    return result


def reset_method_to_todo(skeleton_content: str, method_sig: str, args, fragment: dict) -> str:
    """
    Reset only the failing method to throw Exception('TODO'), preserving other translated methods.

    Args:
        skeleton_content: The current skeleton file content (with failed translation)
        method_sig: Method signature to reset
        args: Command line arguments with model, prompt_type, temperature, project
        fragment: Fragment metadata containing is_test_method

    Returns:
        str: Skeleton content with only the failing method reset to TODO
    """
    print(f"[DEBUG] reset_method_to_todo: Resetting only {method_sig} to TODO", flush=True)

    # Build original skeleton path: data/java/skeletons/{project}/src/...
    project = args.project
    original_base = f"data/java/skeletons/{project}"

    # Determine if this is a test file
    if fragment.get("is_test_method"):
        original_path = os.path.join(original_base, "src", "test")
    else:
        original_path = os.path.join(original_base, "src")

    # Get the class name from fragment
    class_name = fragment.get("class_name", "")
    class_file = f"{class_name}.cj"
    original_file = os.path.join(original_path, class_file)

    print(f"[DEBUG] reset_method_to_todo: original_file = {original_file}", flush=True)

    # Read the original skeleton content (baseline with all TODOs)
    try:
        with open(original_file, 'r') as f:
            original_content = f.read()
        print(f"[DEBUG] reset_method_to_todo: Read {len(original_content)} bytes from original", flush=True)
    except Exception as e:
        print(f"[DEBUG] reset_method_to_todo: Failed to read original: {e}", flush=True)
        return skeleton_content

    # Find the method signature in original content
    sig_start = original_content.find(method_sig)
    if sig_start == -1:
        print(f"[DEBUG] reset_method_to_todo: Method signature not found in original", flush=True)
        return skeleton_content

    # Find the opening brace
    brace_start = original_content.find('{', sig_start)
    if brace_start == -1:
        print(f"[DEBUG] reset_method_to_todo: Opening brace not found", flush=True)
        return skeleton_content

    # Find matching closing brace using stack
    close_brace_pos = -1
    brace_count = 1
    for i in range(brace_start + 1, len(original_content)):
        if original_content[i] == '{':
            brace_count += 1
        elif original_content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                close_brace_pos = i
                break

    if close_brace_pos == -1:
        print(f"[DEBUG] reset_method_to_todo: Closing brace not found", flush=True)
        return skeleton_content

    # Extract the TODO content from original (what's between the braces)
    original_todo_body = original_content[brace_start + 1:close_brace_pos]
    print(f"[DEBUG] reset_method_to_todo: original_todo_body = {repr(original_todo_body)}", flush=True)

    # Now find the same method in skeleton_content (which may have partial translations)
    sig_start_in_skeleton = skeleton_content.find(method_sig)
    if sig_start_in_skeleton == -1:
        print(f"[DEBUG] reset_method_to_todo: Method not found in skeleton", flush=True)
        return original_content

    # Find the opening brace in skeleton_content
    brace_start_in_skeleton = skeleton_content.find('{', sig_start_in_skeleton)
    if brace_start_in_skeleton == -1:
        return original_content

    # Find matching closing brace in skeleton_content
    close_brace_pos_in_skeleton = -1
    brace_count = 1
    for i in range(brace_start_in_skeleton + 1, len(skeleton_content)):
        if skeleton_content[i] == '{':
            brace_count += 1
        elif skeleton_content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                close_brace_pos_in_skeleton = i
                break

    if close_brace_pos_in_skeleton == -1:
        return original_content

    # Replace the method body in skeleton with original TODO
    result = (
        skeleton_content[:brace_start_in_skeleton + 1] +
        original_todo_body +
        skeleton_content[close_brace_pos_in_skeleton:]
    )

    print(f"[DEBUG] reset_method_to_todo: result length = {len(result)}", flush=True)
    return result


def cangjie_compile_with_skeleton(cangjie_code: str, fragment: dict, args) -> tuple:
    """
    Compile Cangjie code by integrating it into the skeleton file.

    This approach:
    1. Reads the skeleton file
    2. Replaces the corresponding function's throw Exception('TODO') with the generated code
    3. Compiles the skeleton
    4. If compilation fails, resets the function back to throw Exception('TODO')

    Args:
        cangjie_code: The generated Cangjie code to compile
        fragment: Fragment metadata containing schema_name, class_name, fragment_name, etc.
        args: Command line arguments

    Returns:
        tuple: (status, feedback, message)
            - status: SUCCESS, ERROR, FAILURE, NOT_EXERCISED
            - feedback: Compiler error information (for LLM retry)
            - message: Compiler output summary
    """
    print(f"[DEBUG] cangjie_compile_with_skeleton called for {fragment.get('class_name', 'unknown')}.{fragment.get('fragment_name', 'unknown')}", flush=True)

    # Get skeleton file path
    skeleton_file = get_skeleton_path(fragment, args)
    print(f"[DEBUG] Skeleton path: {skeleton_file}", flush=True)

    if not os.path.exists(skeleton_file):
        print(f"[DEBUG] Skeleton file not found, falling back to original cangjie_compile", flush=True)
        # Fallback to original behavior if skeleton doesn't exist
        return cangjie_compile(cangjie_code, fragment, args)

    # Read skeleton content
    with open(skeleton_file, 'r') as f:
        skeleton_content = f.read()
    print(f"[DEBUG] Skeleton loaded, content length: {len(skeleton_content)}", flush=True)

    # Find the method in skeleton
    method_sig, start_pos, end_pos = find_method_in_skeleton(skeleton_content, fragment)
    print(f"[DEBUG] find_method_in_skeleton result: sig={method_sig}, start={start_pos}, end={end_pos}", flush=True)

    if method_sig is None:
        print(f"[DEBUG] Method not found in skeleton, falling back to original cangjie_compile", flush=True)
        # Method not found in skeleton, fallback to original behavior
        return cangjie_compile(cangjie_code, fragment, args)

    # Prepare method body - extract just the body from generated code
    # The generated code might include the full method signature, so we need to extract just the body
    method_body = extract_method_body(cangjie_code, fragment)
    print(f"[DEBUG] Extracted method body length: {len(method_body)}", flush=True)
    if args.debug:
        print(f"[DEBUG] Method body preview: {method_body[:200]}...", flush=True)

    # Replace method in skeleton
    modified_skeleton = replace_method_in_skeleton(skeleton_content, method_sig, method_body)
    print(f"[DEBUG] Modified skeleton length: {len(modified_skeleton)}", flush=True)

    # Write modified skeleton to real skeleton file
    with open(skeleton_file, 'w') as f:
        f.write(modified_skeleton)
    print(f"[DEBUG] Modified skeleton written to: {skeleton_file}", flush=True)

    # The project root is data/java/skeletons/{project} which has cjpm.toml
    project_root = os.path.abspath(f"data/java/skeletons/{args.project}")

    try:
        # Call cjc compiler from project root directory
        cmd = [
            'cjc',
            '--diagnostic-format', 'json',
            skeleton_file
        ]
        print(f"[DEBUG] Running cjc compiler on: {skeleton_file}", flush=True)
        print(f"[DEBUG] Working directory: {project_root}", flush=True)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=getattr(args, 'compile_timeout', 60),
            cwd=project_root
        )

        print(f"[DEBUG] cjc return code: {result.returncode}", flush=True)

        # Parse the result
        if result.returncode == 0:
            print(f"[DEBUG] Compilation successful", flush=True)
            return (SUCCESS, None, "Compilation successful")

        # Compilation failed, parse error information
        error_info = parse_cjc_error(result.stderr, result.stdout)
        print(f"[DEBUG] Compilation failed: {error_info[:200]}", flush=True)

        # Reset the method back to throw Exception('TODO') using original skeleton backup
        print(f"[DEBUG] Resetting method to TODO", flush=True)
        reset_skeleton = reset_method_to_todo(skeleton_content, method_sig, args, fragment)
        with open(skeleton_file, 'w') as f:
            f.write(reset_skeleton)

        return (ERROR, error_info, f"Compilation failed: {error_info}")

    except subprocess.TimeoutExpired:
        print(f"[DEBUG] Compilation timeout", flush=True)
        # Reset on timeout
        reset_skeleton = reset_method_to_todo(skeleton_content, method_sig, args, fragment)
        with open(skeleton_file, 'w') as f:
            f.write(reset_skeleton)
        return (ERROR, "Compilation timeout", "Timeout after 60 seconds")
    except Exception as e:
        print(f"[DEBUG] Exception during compilation: {e}", flush=True)
        # Reset on error
        reset_skeleton = reset_method_to_todo(skeleton_content, method_sig, args, fragment)
        with open(skeleton_file, 'w') as f:
            f.write(reset_skeleton)
        return (ERROR, str(e), str(e))


def extract_method_body(cangjie_code: str, fragment: dict) -> str:
    """
    Extract the method body from generated Cangjie code.

    Args:
        cangjie_code: The generated Cangjie code containing full method
        fragment: Fragment metadata

    Returns:
        str: Just the method body (without signature, closing brace, or original indentation)
    """
    fragment_name = fragment.get("fragment_name", "")
    class_name = fragment.get("class_name", "")

    # Extract actual method name - fragment_name might contain line number prefix like "8-11:testMain"
    if ":" in fragment_name:
        method_name = fragment_name.split(":")[-1]
    else:
        method_name = fragment_name

    print(f"[DEBUG] extract_method_body called for fragment_name={fragment_name}, method_name={method_name}, class_name={class_name}", flush=True)
    print(f"[DEBUG] cangjie_code preview: {cangjie_code[:200]}...", flush=True)

    # Determine if this is a top-level function (e.g., main) - these don't have 'func' keyword
    is_top_level_func = (class_name == "main" and method_name == "main")

    # Find the method signature
    # For top-level functions like main, the signature is just "main(...)" without "func"
    # For class methods, the signature is "func methodName(...)"
    if is_top_level_func:
        sig_pattern = rf"{method_name}\s*\([^)]*\)\s*:\s*[^\{{]*"
    else:
        sig_pattern = rf"func\s+{method_name}\s*\([^)]*\)\s*:\s*[^\{{]*"

    print(f"[DEBUG] Using signature pattern: {sig_pattern}", flush=True)
    sig_match = re.search(sig_pattern, cangjie_code)
    if not sig_match:
        print(f"[DEBUG] Method signature not found in generated code", flush=True)
        return cangjie_code.strip()

    # Find the { after the signature
    brace_start = cangjie_code.find('{', sig_match.end() - 1)
    if brace_start == -1:
        print(f"[DEBUG] Opening brace not found", flush=True)
        return cangjie_code.strip()

    # Find matching } using a simple brace-counting approach
    brace_count = 1
    pos = brace_start + 1
    while pos < len(cangjie_code) and brace_count > 0:
        if cangjie_code[pos] == '{':
            brace_count += 1
        elif cangjie_code[pos] == '}':
            brace_count -= 1
        pos += 1

    if brace_count == 0:
        # Extract body between { and }
        body_content = cangjie_code[brace_start + 1:pos - 1]
        # Strip each line - remove leading/trailing whitespace to get pure content
        # This removes original indentation (spaces or tabs)
        lines = body_content.strip().split('\n')
        stripped_lines = [line.strip() for line in lines if line.strip()]
        body = '\n'.join(stripped_lines)
        print(f"[DEBUG] Found method body, length: {len(body)}", flush=True)
        print(f"[DEBUG] Body preview: {body[:100]}...", flush=True)
        return body

    print(f"[DEBUG] Could not find matching closing brace", flush=True)
    return cangjie_code.strip()


def cangjie_compile(cangjie_code: str, fragment: dict, args) -> tuple:
    """
    Use Cangjie compiler (cjc) to validate Cangjie code.

    The compilation process automatically verifies:
    - Syntactic correctness (parser stage)
    - Semantic correctness (semantics stage - fields, types)
    - Executability (code generation)

    Args:
        cangjie_code: The Cangjie code to compile
        fragment: Fragment metadata containing schema_name, class_name, fragment_name, etc.
        args: Command line arguments

    Returns:
        tuple: (status, feedback, message)
            - status: SUCCESS, ERROR, FAILURE, NOT_EXERCISED
            - feedback: Compiler error information (for LLM retry)
            - message: Compiler output summary
    """
    # Determine output directory
    output_dir = getattr(args, 'output_dir', '/tmp/cj_output')
    os.makedirs(output_dir, exist_ok=True)

    # Create temporary file for the Cangjie code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cj', delete=False) as f:
        f.write(cangjie_code)
        temp_file = f.name

    # Generate output file path
    output_file = os.path.join(output_dir, f"{fragment.get('class_name', 'output')}.so")

    try:
        # Call cjc compiler with JSON diagnostic format
        cmd = [
            'cjc',
            '--diagnostic-format', 'json',
            '-o', output_file,
            temp_file
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=getattr(args, 'compile_timeout', 60)
        )

        # Parse the result
        if result.returncode == 0:
            return (SUCCESS, None, "Compilation successful")

        # Compilation failed, parse error information
        error_info = parse_cjc_error(result.stderr, result.stdout)
        return (ERROR, error_info, f"Compilation failed: {error_info}")

    except subprocess.TimeoutExpired:
        return (ERROR, "Compilation timeout", "Timeout after 60 seconds")
    except Exception as e:
        return (ERROR, str(e), str(e))
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def parse_cjc_error(stderr: str, stdout: str) -> str:
    """
    Parse cjc compiler error output and extract useful error messages.

    Args:
        stderr: Standard error output from cjc
        stdout: Standard output from cjc

    Returns:
        str: Formatted error message(s)
    """
    combined_output = stderr + "\n" + stdout

    # Try to parse JSON format errors
    try:
        # Find JSON start position
        json_start = stdout.find('{')
        if json_start != -1:
            json_str = stdout[json_start:]

            # Try to find complete JSON
            brace_count = 0
            json_end = json_start
            for i, char in enumerate(json_str):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = json_start + i + 1
                        break

            json_str = json_str[:json_end - json_start]
            errors = json.loads(json_str)

            # Extract key error information
            error_messages = []
            diagnostics = errors.get('diagnostics', [])

            if not diagnostics:
                # Try alternative format
                for key, value in errors.items():
                    if isinstance(value, dict):
                        msg = value.get('message', str(value))
                        location = value.get('range', {}).get('start', {})
                        line = location.get('line', '?')
                        error_messages.append(f"Line {line}: {msg}")
                    elif isinstance(value, str):
                        error_messages.append(f"{key}: {value}")

            for diag in diagnostics:
                msg = diag.get('message', '')
                location = diag.get('range', {}).get('start', {})
                line = location.get('line', '?')
                column = location.get('column', '?')
                severity = diag.get('severity', 'error')

                error_msg = f"[{severity.upper()}] Line {line}, Col {column}: {msg}"
                error_messages.append(error_msg)

            if error_messages:
                return '\n'.join(error_messages)

    except json.JSONDecodeError:
        pass
    except Exception:
        pass

    # Fallback to raw output
    return combined_output[:2000]  # Limit length


def cangjie_compilation_validation(generation: str, fragment: dict, args) -> tuple:
    """
    Main entry point for Cangjie compilation validation.

    This function combines syntactic, semantic, and executability validation
    into a single compilation step using the cjc compiler.

    The function uses skeleton-based compilation:
    1. Reads the skeleton file for the project
    2. Replaces the corresponding function's throw Exception('TODO') with the generated code
    3. Compiles the skeleton to validate the translation
    4. If compilation fails, resets the function back to throw Exception('TODO')

    Args:
        generation: The generated Cangjie code to validate
        fragment: Fragment metadata
        args: Command line arguments

    Returns:
        tuple: (status, feedback, message)
    """
    # Use skeleton-based compilation
    return cangjie_compile_with_skeleton(generation, fragment, args)
