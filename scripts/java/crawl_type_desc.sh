#!/bin/bash

# ./scripts/java/crawl_type_desc.sh HelloWorld
# ./scripts/java/crawl_type_desc.sh Calculator
# ./scripts/java/crawl_type_desc.sh commons-fileupload

if [ $# -ne 1 ]; then
  echo "Usage: ./scripts/java/crawl_type_desc.sh <project>"
  exit 1
fi

project=$1

echo "crawling type description for $project"
python3 src/java/type_resolution/crawl_type_desc.py --project=$project

