#!/bin/bash

# ./scripts/java/translate_types.sh simple-calculator _decomposed_tests
# ./scripts/java/translate_types.sh commons-fileupload _decomposed_tests

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/extract_types.sh <project> <model_name> <type>"
  exit 1
fi

project=$1
type=$2
model_name=$3

echo "translating types for $project"
python3 src/java/type_resolution/translate_type.py --project_name=$project --model_name=$model_name --type=$type
