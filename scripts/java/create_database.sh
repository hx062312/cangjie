#!/bin/bash

# ./scripts/java/create_database.sh calculator _decomposed_tests
# ./scripts/java/create_database.sh commons-fileupload _decomposed_tests
# ./scripts/java/create_database.sh HelloWorld _decomposed_tests

if [ $# -ne 2 ]; then
  echo "Usage: ./scripts/java/create_database.sh <project> <suffix>"
  exit 1
fi

project=$1
suffix=$2

mkdir -p databases;
main=$(pwd);
projects_dir=projects/java/cleaned_final_projects${suffix};


echo "creating database $project"
cd "$projects_dir/$project" || exit
codeql database create ../../../../databases/${project}${suffix} --language=java --overwrite;
cd "$main" || exit
