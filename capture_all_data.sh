#!/bin/bash

# Define parameters.
duration=300
background_flows=6
input_file="connection_parameter_combinations.csv"

while IFS="," read -r bw delay bdp cc_algo scenario
do
    trimmed_scenario=$(echo "$scenario" | tr -d '[:space:]')
    trimmed_cc=$(echo "$cc_algo" | tr -d '[:space:]')
    ./data_capture.sh -d "$duration" -c "$trimmed_cc" -n "$background_flows" -l "$delay" -b "$bw" -q "$bdp" -s "$trimmed_scenario"
done < "$input_file"
