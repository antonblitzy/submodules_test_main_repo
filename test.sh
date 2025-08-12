#!/bin/bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <repo_path>" >&2
    exit 1
fi

REPO_PATH="$1"
if [ ! -d "$REPO_PATH" ]; then
    echo "Error: $REPO_PATH is not a directory" >&2
    exit 1
fi

cd "$REPO_PATH"

DIRS=(
    "."
    "subrepos/subrepo_1"
    "subrepos/subrepo_2"
    "subrepo_3"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$REPO_PATH/$dir" ]; then
        echo "Error: $dir does not exist" >&2
        exit 1
    fi
    
   
    ISO_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    COMMITTED_FILE="$REPO_PATH/$dir/committed_${ISO_TIME}"
    UNCOMMITTED_FILE="$REPO_PATH/$dir/uncommitted_${ISO_TIME}"

    cd "$REPO_PATH/$dir"
    
    touch "$COMMITTED_FILE"
    touch "$UNCOMMITTED_FILE"
    
    git add "committed_${ISO_TIME}"
    git commit -m "Add committed file at ${ISO_TIME}"
    cd "$REPO_PATH"
done
