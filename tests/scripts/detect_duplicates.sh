#!/bin/bash

# for file in *.ndjson; do ./detect_duplicates.sh "$file"; done

detect_duplicates() {
    local ndjson_file=$1

    if [[ ! -f $ndjson_file ]]; then
        echo "File not found: $ndjson_file"
        exit 1
    fi

    sort "$ndjson_file" | uniq -d > duplicates.txt

    if [[ -s duplicates.txt ]]; then
        echo "Duplicate rows found:"
        cat duplicates.txt
    else
        echo "No duplicate rows found."
    fi

    rm duplicates.txt
}

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <ndjson_file>"
    exit 1
fi

detect_duplicates "$1"