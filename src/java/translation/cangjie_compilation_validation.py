import json
import os
import subprocess
import tempfile

from src.compositional_glue_tests.script import ERROR, FAILURE, NOT_EXERCISED, SUCCESS


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

    Args:
        generation: The generated Cangjie code to validate
        fragment: Fragment metadata
        args: Command line arguments

    Returns:
        tuple: (status, feedback, message)
    """
    return cangjie_compile(generation, fragment, args)
