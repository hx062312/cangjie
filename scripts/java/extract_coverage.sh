#!/bin/bash

# ./scripts/java/extract_coverage.sh simple-calculator _decomposed_tests
# ./scripts/java/extract_coverage.sh commons-fileupload _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/extract_coverage.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

echo "extracting test coverage for $project"
python3 src/java/static_analysis/extract_source_tests.py --project_name=$project --suffix=$suffix
