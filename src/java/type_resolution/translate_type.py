import argparse
import json
import tqdm
import subprocess
import os
import re
import yaml
import logging
from openai import OpenAI


def prompt_model(model_info, client, prompt, args):

    completion = client.chat.completions.create(
        model=model_info[args.model_name]["model_id"],
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.0,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
    )

    generation = completion.choices[0].message.content

    return generation


def main(args):

    model_info = yaml.safe_load(open("configs/model_configs.yaml", "r"))["models"]

    if not os.path.exists(f"data/java/type_resolution/universal_type_map_final.json"):
        with open(f"data/java/type_resolution/universal_type_map_final.json", "w") as f:
            json.dump({}, f)

    universal_type_map = {}
    with open(f"data/java/type_resolution/universal_type_map_final.json", "r") as f:
        universal_type_map = json.load(f)

    logging.basicConfig(
        filename=f"data/java/type_resolution/{args.project_name}/{args.type}.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(module)s - %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.info("new run started...")

    in_fname = f"data/java/type_resolution/{args.project_name}/s1_input.json"
    out_fname = f"data/java/type_resolution/{args.project_name}/s1_output.json"

    if args.type == "source_description":
        in_fname = f"data/java/type_resolution/{args.project_name}/s1_output.json"
        out_fname = f"data/java/type_resolution/{args.project_name}/s2_output.json"

    types = {}
    with open(in_fname, "r") as f:
        types = json.load(f)

    type_description = {}
    try:
        with open(
            f"data/java/type_resolution/{args.project_name}/type_description.json", "r"
        ) as f:
            type_description = json.load(f)
    except FileNotFoundError:
        type_description = {}

    index = 0
    max_attempts = 5
    total_failed = 0
    total_success = 0
    total_overturning_attempts = []
    include_feedback = False
    feedback = ""
    pbar = tqdm.tqdm(total=len(types))
    while index < len(types):
        if max_attempts == 0:
            logging.info(f"Failed to translate {type_}... skipping")
            total_failed += 1
            index += 1
            include_feedback = False
            feedback = ""
            max_attempts = 5
            universal_type_map[type_] = ""
            pbar.update(1)
            continue

        type_ = list(types.keys())[index]

        if type_ in universal_type_map and universal_type_map[type_] != "":
            assert universal_type_map[type_].strip() != ""
            logging.info(f"{type_} already translated to {universal_type_map[type_]}")
            types[type_] = universal_type_map[type_]
            index += 1
            total_success += 1
            pbar.update(1)
            continue

        if types[type_] != "":
            index += 1
            universal_type_map[type_] = types[type_]
            pbar.update(1)
            continue

        # Few-shot examples for Cangjie (same format as original Python version)
        icl = """Java type:
```
String
```

Cangjie type:
```
String
```

Java type:
```
int
```

Cangjie type:
```
Int64
```

Java type:
```
List<String>
```

Cangjie type:
```
Array<String>
```

Java type:
```
Map<String, Integer>
```

Cangjie type:
```
HashMap<String, Int64>
```

Java type:
```
Optional<String>
```

Cangjie type:
```
?String
```"""

        instruction = f"""### Instruction:
Translate the following Java type to Cangjie language type and write your response like the example above:

Java type:
```
{type_}
```

### Response:
Cangjie type:
"""

        if args.type == "source_description" and type_ in type_description:
            description = type_description[type_]["summarized_text"].replace("\n", "")
            instruction = instruction.replace(
                "### Instruction:\nTranslate the following Java type to Cangjie language type and write your response like the example above:",
                f"### Instruction:\nTranslate the following Java type to Cangjie language type and write your response like the example above. A description of Java type is given as well:\n\nType Description:\n{description}"
            )

            if include_feedback:
                instruction = instruction.replace(
                    f"A description of Java type is given as well:\n\nType Description:\n{description}",
                    f"Your previous translation attempt was incorrect. Here is the feedback:\n\n{feedback}\n\nA description of Java type is given as well:\n\nType Description:\n{description}"
                )

        elif args.type == "simple":
            if include_feedback:
                instruction = instruction.replace(
                    "### Instruction:\nTranslate the following Java type to Cangjie language type and write your response like the example above:",
                    f"Your previous translation attempt was incorrect. Here is the feedback:\n\n{feedback}\n\n### Instruction:\nTranslate the following Java type to Cangjie language type and write your response like the example above:"
                )

        prompt = f"{icl}\n\n{instruction}"

        logging.info("*" * 100)
        logging.info(prompt)
        logging.info("*" * 100)

        client = OpenAI(
            **{
                k: v
                for k, v in model_info[args.model_name].items()
                if k in ["api_key", "base_url", "default_headers"]
            }
        )

        generation = prompt_model(model_info, client, prompt, args)

        # Debug: log raw response
        logging.info(f"Raw LLM response: {generation[:500]}...")

        # Same parsing logic as original Python code
        generation = generation.replace("```cangjie", "```")
        generation = generation.replace("```cj", "```")
        pattern = r"```((?:[^`]|`[^`]|``[^`])*?)```"
        match = re.search(pattern, generation, re.DOTALL)

        if not match:
            logging.info(f"Failed to translate {type_} - no code block found")
            max_attempts -= 1
            continue

        generation = match.group(1).strip()

        if generation == "":
            logging.info(f"Failed to translate {type_} - empty translation")
            max_attempts -= 1
            continue

        logging.info(f"Parsed translation: {generation}")

        # Replace generic type parameters with Any (Cangjie's placeholder type)
        pattern = re.compile(r"\bV\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bE\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bC\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bP\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bWE\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bR\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bD\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bK\b")
        generation = pattern.sub("Any", generation)

        pattern = re.compile(r"\bF\b")
        generation = pattern.sub("Any", generation)

        # Read template and replace placeholder (same logic as original)
        template_path = f"data/java/templates/{args.project_name}/template.cj"
        with open(template_path, "r") as f:
            cangjie_program = f.read()

        cangjie_program = cangjie_program.replace("<placeholder>", generation)

        with open("test.cj", "w") as f:
            f.write(cangjie_program)

        # Compile check (same as original py_compile)
        try:
            subprocess.run(
                ["cjc", "test.cj"],
                check=True,
                capture_output=True,
                timeout=60,
            )

        except subprocess.CalledProcessError as e:
            logging.info(f"compile error for translated type {generation}... trying again for {type_}")
            # cjc outputs errors to stdout, not stderr
            error_output = e.stdout if e.stdout else (e.stderr if e.stderr else "Unknown error")
            logging.info(f"Compiler output: {error_output}")
            feedback = f"The translated type '{generation}' is syntactically incorrect in Cangjie.\n\n{error_output}"
            feedback = "\n".join(feedback.strip().split("\n")[-2:])
            include_feedback = True
            max_attempts -= 1
            if os.path.exists("test.cj"):
                os.remove("test.cj")
            continue

        except FileNotFoundError:
            logging.info(f"cjc compiler not found, skipping validation")
            # If compiler not found, still accept the translation

        if os.path.exists("test.cj"):
            os.remove("test.cj")

        logging.info(f"Translated {type_} to {generation}")

        pbar.update(1)
        total_success += 1
        types[type_] = generation
        universal_type_map[type_] = generation
        index += 1
        total_overturning_attempts.append(5 - max_attempts)
        max_attempts = 5
        include_feedback = False
        feedback = ""

    with open(out_fname, "w") as f:
        json.dump(types, f, indent=4)

    with open(f"data/java/type_resolution/universal_type_map_final.json", "w") as f:
        json.dump(universal_type_map, f, indent=4)

    logging.info(f"Total success: {total_success}")
    logging.info(f"Total failed: {total_failed}")
    if total_overturning_attempts != []:
        logging.info(
            f"Average attempts to overturn: {sum(total_overturning_attempts) / len(total_overturning_attempts)}"
        )


if __name__ == "__main__":
    parser_ = argparse.ArgumentParser(
        description="Translate java types to cangjie types"
    )
    parser_.add_argument(
        "--project_name", type=str, dest="project_name", help="project name"
    )
    parser_.add_argument(
        "--model_name",
        type=str,
        dest="model_name",
        help="model name to use for translation",
    )
    parser_.add_argument("--type", type=str, dest="type", help="translation type")
    args = parser_.parse_args()
    main(args)
