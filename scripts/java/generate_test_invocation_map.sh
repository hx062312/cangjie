#!/bin/bash

# ./scripts/java/generate_test_invocation_map.sh simple-calculator gpt-4o-2024-11-20 _decomposed_tests
# ./scripts/java/generate_test_invocation_map.sh commons-fileupload gpt-4o-2024-11-20 _decomposed_tests

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/generate_test_invocation_map.sh <project> <model> <suffix>"
  exit 1
fi

project=$1
model=$2
suffix=$3

echo "extracting test map for $project"
python3 src/java/static_analysis/create_test_method_map.py --project_name=$project --model_name=$model --suffix=$suffix
