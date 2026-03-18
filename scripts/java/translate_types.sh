#!/bin/bash

# ./scripts/java/translate_types.sh HelloWorld gpt-4o-2024-11-20 simple
# ./scripts/java/translate_types.sh Calculator gpt-4o-2024-11-20 simple
# ./scripts/java/translate_types.sh commons-fileupload gpt-4o-2024-11-20 simple

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/translate_types.sh <project> <model_name> <type>"
  exit 1
fi

project=$1
model=$2
type=$3

echo "translating types for $project"
python3 src/java/type_resolution/translate_type.py --project=$project --model=$model --type=$type
