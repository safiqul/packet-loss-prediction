#!/bin/bash

# Define the constant parts of the path
BASE_PATH="output/reno/fix_pacing_rate/without_timestamps/single_flow"
SCRIPT_NAME="parse_pcap.py"
SOURCE_IP="10.1.1.100"
DURATION="60"

# Define the arrays for the variable parts of the path
declare -a Thresholds=("0.1th" "0.25th" "0.5th" "no_model_inference")
declare -a Delays=("30ms")
declare -a Bandwidths=("10mbit" "50mbit")
declare -a QueueSizes=("0.25bdp" "0.5bdp" "1bdp")
declare -a Runs=("first_run" "second_run" "third_run" "fourth_run" "fifth_run")

# Loop through the combinations of thresholds, delays, bandwidths, queue sizes, and runs
for threshold in "${Thresholds[@]}"; do
    for delay in "${Delays[@]}"; do
        for bandwidth in "${Bandwidths[@]}"; do
            for queue_size in "${QueueSizes[@]}"; do
                for run in "${Runs[@]}"; do
                    # Construct the file paths
                    pcap_file="${BASE_PATH}/${threshold}/${delay}/${bandwidth}/${queue_size}/${run}/tshark_data.pcap"
                    output_file="${BASE_PATH}/${threshold}/${delay}/${bandwidth}/${queue_size}/${run}/metrics.txt"

                    # Run the Python script with the constructed file paths
                    python "${SCRIPT_NAME}" -i "${pcap_file}" -o "${output_file}" -d "${DURATION}" -s "${SOURCE_IP}"
                done
            done
        done
    done
done
