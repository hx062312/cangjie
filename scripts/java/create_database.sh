#!/bin/bash

# ./scripts/java/create_database.sh simple-calculator _decomposed_tests java
# ./scripts/java/create_database.sh commons-fileupload _decomposed_tests java

if [ $# -ne 3 ]; then
  echo "Usage: ./scripts/java/create_database.sh simple-calculator <suffix> <language>"
  exit 1
fi

project=$1
suffix=$2
language=$3

mkdir -p databases;
main=$(pwd);
projects_dir=projects/$language/cleaned_final_projects${suffix};


echo "creating database $project"
cd "$projects_dir/$project" || exit
codeql database create ../../../../databases/${project}${suffix} --language=$language --overwrite;
cd "$main" || exit
