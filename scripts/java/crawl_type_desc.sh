#!/bin/bash

# ./scripts/java/crawl_type_desc.sh simple-calculator _decomposed_tests
# ./scripts/java/crawl_type_desc.sh commons-fileupload _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/crawl_type_desc.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

echo "crawling type description for $project"
python3 src/java/type_resolution/crawl_type_desc.py --project_name=$project

