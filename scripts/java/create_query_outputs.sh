#!/bin/bash

# ./scripts/java/create_query_outputs.sh calculator _decomposed_tests
# ./scripts/java/create_query_outputs.sh commons-fileupload _decomposed_tests
# ./scripts/java/create_query_outputs.sh HelloWorld _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/create_query_outputs.sh <project> <suffix>"
  exit 1
fi

project_root="$(pwd)"

project="$1"
suffix="$2"

database="${project}${suffix}"

codeql_dir="$project_root/vscode-codeql-starter/codeql-custom-queries-java"
output_dir="data/java/query_outputs_decomposed_tests"
cd "$codeql_dir" || exit 1


echo "=========================================="
echo "Running CodeQL queries for: $project"
echo "Database:      $database"
echo "Output:        $output_dir"
echo "=========================================="

bash execute_codeql_queries.sh "$project" "$database" "$output_dir"

echo "Done! Results saved to: $output_dir"
