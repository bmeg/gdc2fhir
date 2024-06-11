#!/bin/bash

input_file=$1
output_file=$2
pattern="TCGA-BRCA"

grep "$pattern" "$input_file" > "$output_file"
echo "Filtered lines containing '$pattern' are stored in '$output_file'."
