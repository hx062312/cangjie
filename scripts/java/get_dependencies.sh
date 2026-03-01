#!/bin/bash

# ./scripts/java/get_dependencies.sh simple-calculator _decomposed_tests
# ./scripts/java/get_dependencies.sh commons-fileupload _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/get_dependencies.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

echo "extracting dependencies for $project"
python3 utils.py --project_name=$project --function=parse_dependencies --suffix=$suffix
