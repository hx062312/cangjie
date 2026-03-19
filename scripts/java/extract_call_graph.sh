#!/bin/bash

# ./scripts/java/extract_call_graph.sh calculator _decomposed_tests
# ./scripts/java/extract_call_graph.sh commons-fileupload _decomposed_tests
# ./scripts/java/extract_call_graph.sh HelloWorld _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/extract_call_graph.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

python3 src/java/static_analysis/extract_call_graph.py --project=$project --suffix=$suffix

