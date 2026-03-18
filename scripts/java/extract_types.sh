#!/bin/bash

# ./scripts/java/extract_types.sh HelloWorld _decomposed_tests
# ./scripts/java/extract_types.sh Calculator _decomposed_tests
# ./scripts/java/extract_types.sh commons-fileupload _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/extract_types.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

echo "extracting types for $project"
python3 src/java/type_resolution/extract_types.py --project=$project --suffix=$suffix

