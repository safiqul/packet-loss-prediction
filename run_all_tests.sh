#!/bin/bash

duration=60
cc_algorithm="reno"
bg_flows=6
delay=30
scenario="half"
input_file="test_parameter_combinations.csv"

while IFS="," read -r bandwidth_raw queue_size_raw threshold_raw
do
    bandwidth=$(echo "$bandwidth_raw" | tr -d '[:space:]')
    queue_size=$(echo "$queue_size_raw" | tr -d '[:space:]')
    threshold=$(echo "$threshold_raw" | tr -d '[:space:]')

    model_inference_flag=""
    threshold_flag=""

    if [ "$threshold" = "0.1" ] || [ "$threshold" = "0.25" ] || [ "$threshold" = "0.5" ]; then
        model_inference_flag="-m 1"
        threshold_flag="-t $threshold"
        echo "Model inference should be turned on"
    elif [ "$threshold" = "1" ]; then
        model_inference_flag=""
        threshold_flag=""
    fi

    echo "Running test with bandwidth: $bandwidth, queue size: $queue_size, and threshold: $threshold"

    ./start_and_run_connection.sh -d "$duration" -c "$cc_algorithm" -n "$bg_flows" -l "$delay" -s "$scenario" -b "$bandwidth" -q "$queue_size" $model_inference_flag $threshold_flag

    sleep 10

done < "$input_file"
