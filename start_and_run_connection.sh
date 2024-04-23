#!/bin/bash
source ./bash_functions.sh

# Set default values.
duration=300
cc_algorithm="reno"
bg_flows=0
delay=50
bandwidth=50
queue_size=1.0  # 1 BDP
scenario="reno"
model_inference=0
threshold=0.5
timestamp_mode=0

# Print usage.
usage() {
    echo "Usage: $0 [-d <duration>] [-c <congestion control algorithm>] [-n <number of background flows>] [-l <delay>] [-b <bandwidth>] [-q <queue size>] [-s <scenario>] [-m <enable model inference>] [-t <classification threshold>] [-z <timestamp mode>]" 1>&2
    echo "  -d: Duration in seconds (default: $duration)"
    echo "  -c: Congestion control algorithm. Valid options are 'cubic', 'reno', and 'bbr' (default: $cc_algorithm)"
    echo "  -n: Number of background flows. Valid options are 0-6 (default: $bg_flows)"
    echo "  -l: Delay in milliseconds (default: $delay)"
    echo "  -b: Bandwidth in Mbit/s (default: $bandwidth)"
    echo "  -q: Queue size in multipliers of BDP (default: $queue_size)"
    echo "  -s: Scenario to run (default: $scenario). Supported options are 'reno', 'cubic', and, 'half', where 'half' runs half the number of background flows as Reno and half as Cubic."
    echo "  -m: Model inference flag. 0 for false and 1 for true (default: $model_inference)"
    echo "  -t: Classification threshold for predictions when model inference is enabled. should be a float value (default: $threshold)"
    echo "  -z: Timestamp mode flag. 0 for false and 1 for true (default: $timestamp_mode)"
    exit 1
}

# Parse arguments.
while getopts ":d:c:n:l:b:q:s:m:t:a:z:" opt; do
    case ${opt} in
        d)
            duration=$OPTARG
            ;;
        c)
            cc_algorithm=$OPTARG
            ;;
        n)
            bg_flows=$OPTARG
            ;;
        l)
            delay=$OPTARG
            ;;
        b)
            bandwidth=$OPTARG
            ;;
        q)
            queue_size=$OPTARG
            ;;
        s)
            scenario=$OPTARG
            ;;
        m)
            model_inference=$OPTARG
            ;;
        t)
            threshold=$OPTARG
            ;;
        z)
            timestamp_mode=$OPTARG
            ;;
        \?)
            usage
            ;;
        :)
            echo "Invalid option: $OPTARG requires an argument" 1>&2
            usage
            ;;
    esac
done
shift $((OPTIND -1))

# Check if values are valid.
if ! [[ "$duration" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid duration value. Please provide a positive integer value."
    exit 1
fi
if ! [[ "$cc_algorithm" =~ ^(cubic|reno|bbr)$ ]]; then
    echo "Error: Invalid congestion control algorithm. Valid options are 'cubic', 'reno', and 'bbr'."
    exit 1
fi
if ! [[ "$bg_flows" =~ ^[0-6]$ ]]; then
    echo "Error: Invalid number of background flows. Valid options are 0-6."
    exit 1
fi
if ! [[ "$delay" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid delay value. Please provide a positive integer value."
    exit 1
fi
if ! [[ "$bandwidth" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid bandwidth value. Please provide a positive integer value."
    exit 1
fi
if ! [[ "$queue_size" =~ ^[0-9]*\.?[0-9]+$ ]]; then
    echo "Error: Invalid queue size value. Please provide a positive float value."
    exit 1
fi
if ! [[ "$scenario" =~ ^(cubic|reno|half)$ ]]; then
    echo "Error: Invalid scenario. Valid options are 'cubic', 'reno', and 'half'."
    exit 1
fi
if ! [[ "$model_inference" =~ ^[0-1]$ ]]; then
    echo "Error: Invalid model inference flag. Valid options are 0 (for false) or 1 (for true)."
    exit 1
fi
if ! [[ "$threshold" =~ ^[0-9]*\.?[0-9]+$ ]]; then
    echo "Error: Invalid threshold value. Please provide a float value."
    exit 1
fi
if ! [[ "$timestamp_mode" =~ ^[0-1]$ ]]; then
    echo "Error: Invalid timestamp mode flag. Valid options are 0 (for false) or 1 (for true)."
    exit 1
fi

queue_size=$(calculate_queue_size $delay $bandwidth $queue_size)

inference_label=""
if [ "$model_inference" -eq 1 ]; then
    inference_label="model_inference"
else
    inference_label="no_model_inference"
fi

directory_path="output/tests/${cc_algorithm}_${bg_flows}bg_${delay}ms_${bandwidth}mbit_${queue_size}bytes_${duration}s_${inference_label}_${threshold}th"
output_file_path_prediction_module=""

read -sp "Enter sudo password: " password
echo ""

echo "$password" | sudo -S mkdir -p "$directory_path"
echo "$password" | sudo -S chmod -R 777 "$directory_path"

if [ "$model_inference" -eq 1 ]; then
    # Start the data persistence daemon.
    input_file_path_data_persistence_module="${directory_path}/ss_data_predict.txt"
    output_file_path_data_persistence_module="${directory_path}/input_data.csv"

    gnome-terminal --window --title="Data Persistence Module" \
    -- bash -c "python ../../tests/test_setup/prepare_data.py -d \"$directory_path\" -i \"$input_file_path_data_persistence_module\" -o \"$output_file_path_data_persistence_module\"" &

    # Start the prediction daemon.
    classifier_name="binary_clf_${cc_algorithm}_phase_three.ubj"
    classifier_path_prediction_module="../../ml_model/single_flow/models/${cc_algorithm}/${classifier_name}"
    input_file_path_prediction_module="${output_file_path_data_persistence_module}"
    output_file_path_prediction_module="${directory_path}/prediction.txt"

    timestamp_flag=""
    if [ "$timestamp_mode" -eq 1 ]; then
        timestamp_flag="--timestamp_mode"
    fi

    gnome-terminal --window --title="Prediction Module" \
    -- bash -c "python ../../tests/test_setup/predict.py -c \"$classifier_path_prediction_module\" -d \"$directory_path\" -i \"$input_file_path_prediction_module\" -o \"$output_file_path_prediction_module\" -t \"$threshold\" $timestamp_flag" &
fi

# Start Mininet and run iperf.
toggle_ecn=$((1 - timestamp_mode))
gnome-terminal --window --title="Mininet" \
-- bash -c "echo $password | sudo -S bash -c 'source ./bash_functions.sh; start_and_run_connection_and_collect_data $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $model_inference $output_file_path_prediction_module $directory_path $toggle_ecn';" &

# Print message to user.
echo "Connection started with the following parameters:"
echo "Duration: $duration seconds"
echo "Congestion control algorithm: $cc_algorithm"
echo "Number of background flows: $bg_flows"
echo "Delay: $delay ms"
echo "Bandwidth: $bandwidth Mbit/s"
echo "Queue size: $queue_size bytes"
echo "Scenario: $scenario"
echo "Model inference: $model_inference"
echo "Threshold: $threshold"
echo "Timestamp mode: $timestamp_mode"

# Print progress.
start_time=$(date +%s)
while true; do
    current_time=$(date +%s)
    elapsed_time=$((current_time - start_time))
    percentage=$((elapsed_time * 100 / duration))
    elapsed_time_formatted=$(printf '%02d:%02d' $((elapsed_time / 60)) $((elapsed_time % 60)))
    remaining_time_formatted=$(printf '%02d:%02d' $(((duration - elapsed_time) / 60)) $(((duration - elapsed_time) % 60)))
    printf "\r%d%% (%s / %s)" \
           "$percentage" \
           "$elapsed_time_formatted" \
           "$remaining_time_formatted"
    if (( elapsed_time >= duration )); then
        break
    fi
    sleep 1
done

echo ""

echo "Connection closed. Output saved to ${directory_path}/ss_data.txt"

get_metrics "output/pcap/tshark_data.pcap" "$cc_algorithm" "$bg_flows" "$delay" "$bandwidth" "$queue_size" "$scenario" "$duration" "$model_inference" "$threshold" "$directory_path"

echo "Metrics saved to ${directory_path}/metrics.txt"

python_script_path="../../tests/test_setup/create_cwnd_plot.py"

cmd="python \"$python_script_path\" \
    -i \"${directory_path}/ss_data.txt\" \
    -b \"$bandwidth\" \
    -d \"$delay\" \
    -q \"$queue_size\" \
    -t \"$duration\" \
    -o \"${directory_path}\""

if [ "$model_inference" -eq 1 ]; then
    cmd+=" --model_inference"
    cmd+=" -c \"$threshold\""
fi

cmd+=" --show"

eval "$cmd"

echo "cwnd plot created and saved to ${directory_path}"
