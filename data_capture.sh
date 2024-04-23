#!/bin/bash

# Set default values.
duration=300
cc_algorithm="cubic"
bg_flows=0
delay=50
bandwidth=50
queue_size=312500
scenario="reno"

# Print usage.
usage() {
    echo "Usage: $0 [-d <duration>] [-c <congestion control algorithm>] [-n <number of background flows>] [-l <delay>] [-b <bandwidth>] [-q <queue size>]" 1>&2
    echo "  -d: Duration in seconds (default: $duration)"
    echo "  -c: Congestion control algorithm. Valid options are 'cubic', 'reno', and 'bbr' (default: $cc_algorithm)"
    echo "  -n: Number of background flows. Valid options are 0-6 (default: $bg_flows)"
    echo "  -l: Delay in milliseconds (default: $delay)"
    echo "  -b: Bandwidth in Mbit/s (default: $bandwidth)"
    echo "  -q: Queue size in packets (default: $queue_size)"
    echo "  -s: Scenario to run (default: $scenario). Supported options are 'reno', 'cubic', and, 'half', where 'half' runs half the number of background flows as Reno and half as Cubic."
    exit 1
}

# Parse arguments.
while getopts ":d:c:n:l:b:q:s:" opt; do
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
if ! [[ "$queue_size" =~ ^[0-9]+$ ]]; then
    echo "Error: Invalid queue size value. Please provide a positive integer value."
    exit 1
fi
if ! [[ "$scenario" =~ ^(cubic|reno|half)$ ]]; then
    echo "Error: Invalid scenario. Valid options are 'cubic', 'reno', and 'half'."
    exit 1
fi

directory_path="output/text/${cc_algorithm}/${bg_flows}bg_flows/${delay}ms_${bandwidth}mbit_${queue_size}bytes_${duration}s"

# Start Mininet and run iperf.
read -sp "Enter sudo password: " password
echo ""

echo "$password" | sudo -S mkdir -p "$directory_path"
echo "$password" | sudo -S chmod -R 777 "$directory_path"

gnome-terminal --window --title="Mininet" \
-- bash -c "echo $password | sudo -S bash -c 'source ./bash_functions.sh; start_mininet_and_run_iperf $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $directory_path';" &

# Print message to user.
echo "Data capture procedure started with the following parameters:"
echo "Duration: $duration seconds"
echo "Congestion control algorithm: $cc_algorithm"
echo "Number of background flows: $bg_flows"
echo "Delay: $delay ms"
echo "Bandwidth: $bandwidth Mbit/s"
echo "Queue size: $queue_size packets"
echo "Scenario: $scenario"

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

echo "Data capture procedure finished. Output saved to data_pipeline/data_capture/output/text/${cc_algorithm}/${bg_flows}bg_flows"


