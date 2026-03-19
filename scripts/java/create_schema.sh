#!/bin/bash

# ./scripts/java/create_schema.sh calculator _decomposed_tests
# ./scripts/java/create_schema.sh commons-fileupload _decomposed_tests
# ./scripts/java/create_schema.sh HelloWorld _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/create_schema.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

echo "creating schema for $project"
python3 src/java/static_analysis/create_schema.py --project=$project --suffix=$suffix
