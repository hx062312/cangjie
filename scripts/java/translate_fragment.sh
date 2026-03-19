#!/bin/bash

# ./scripts/java/translate_fragment.sh calculator gpt-4o-2024-11-20 0.0
# ./scripts/java/translate_fragment.sh commons-fileupload gpt-4o-2024-11-20 0.0
# ./scripts/java/translate_fragment.sh HelloWorld gpt-4o-2024-11-20 0.0

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/translate_fragment.sh <project> <model> <temperature>"
  exit 1
fi

project=$1
model=$2
temperature=$3


export PYTHONPATH=$PYTHONPATH:`pwd`/src/java/translation
python3 src/java/translation/compositional_translation_validation.py \
    --model=$model \
    --project=$project \
    --from_lang=Java \
    --to_lang=Cangjie \
    --include_call_graph \
    --debug \
    --suffix=_decomposed_tests \
    --temperature=$temperature \
    --validate_by_cangjie \
    --recursion_depth=2 \
    --include_implementation | tee ${project}_${model}_body.log
