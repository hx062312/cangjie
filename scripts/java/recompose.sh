#!/bin/bash

# ./scripts/java/recompose.sh simple-calculator gpt-4o-2024-11-20 0.0
# ./scripts/java/recompose.sh commons-fileupload gpt-4o-2024-11-20 0.0
# ./scripts/java/recompose.sh hello-world gpt-4o-2024-11-20 0.0

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/recompose.sh <project> <model> <temperature>"
  exit 1
fi

project=$1
model=$2
temperature=$3


python3 src/postprocessing/recompose.py --project=$project \
                                            --model=$model \
                                            --output_dir=data/java/recomposed_projects \
                                            --type=body \
                                            --temperature=$temperature \
                                            --suffix=_decomposed_tests

