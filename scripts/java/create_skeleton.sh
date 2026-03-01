#!/bin/bash

# ./scripts/java/create_skeleton.sh simple-calculator gpt-4o-2024-11-20 signature _decomposed_tests 0.0
# ./scripts/java/create_skeleton.sh commons-fileupload gpt-4o-2024-11-20 signature _decomposed_tests 0.0

if [ $# -ne 5 ]; then
  echo "Usage: ./scripts/java/create_skeleton.sh <project> <model> <type> <suffix> <temperature>"
  exit 1
fi

project=$1
model=$2
type=$3
suffix=$4
temperature=$5

pwd=$(pwd)

echo "creating skeleton for $project"
export PYTHONPATH=$pwd/data/skeletons/$project
python3 src/java/static_analysis/create_skeleton.py --project_name=$project --model_name=$model --type=$type --suffix=$suffix --temperature=$temperature