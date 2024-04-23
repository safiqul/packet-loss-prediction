#!/bin/bash

# Starts Mininet with optional parameters for congestion control algorithm, delay,
# bandwidth, queue size, background flows, packet loss prediction file path, and model inference flag.
# If no parameters are provided, default values are used.
# Parameters:
# $1: Congestion control algorithm to use (default: cubic).
# $2: Delay to use in ms (default: 50).
# $3: Bandwidth to use in Mbit (default: 50).
# $4: Queue size to use (default: 312500).
# $5: Number of background flows to use (default: 0).
# $6: Model inference flag (default: 0).
# $7: Path to the file containing the packet loss prediction (default: "").
start_mininet() {
    local algorithm=${1:-cubic}
    local delay=${2:-50}
    local bandwidth=${3:-50}
    local queue_size=${4:-312500}
    local bg_flows=${5:-0}
    local model_inference=${6:-0}
    local prediction_file_path=${7:-""}

    if [[ "$model_inference" == "1" ]]; then
        sudo python3 mn_topo.py -a "$algorithm" -d "$delay" -b "$bandwidth" -q "$queue_size" -f "$bg_flows" --model_inference -i "$prediction_file_path"
    else
        sudo python3 mn_topo.py -a "$algorithm" -d "$delay" -b "$bandwidth" -q "$queue_size" -f "$bg_flows"
    fi
}


# Pipe the output from echo to the mew_start_mininet function to automatically start mininet and run the given amount of pings.
start_mininet_with_args_and_run_pings() {
	echo "h1 hping3 --count 10 h2" | start_mininet
}


# Starts Mininet and runs iperf for the specified duration with the specified congestion control algorithm and number of background flows.
# Optional parameters for delay, bandwidth, and queue size can also be specified.
# If no parameters are provided, default values are used.
# Parameters:
# $1: Duration for iperf to run for in seconds (default: 600).
# $2: Congestion control algorithm to use (default: cubic).
# $3: Number of background flows to use (default: 0).
# $4: Delay to use in ms (default: 50).
# $5: Bandwidth to use in Mbit (default: 50).
# $6: Queue size to use (default: 312500).
# $7: Scenario to use (default: reno).
# $8: Directory path where the output file should be saved.
start_mininet_and_run_iperf() {
    local duration=${1:-600}
    local algorithm=${2:-cubic}
    local bg_flows=${3:-0}
    local delay=${4:-50}
    local bandwidth=${5:-50}
    local queue_size=${6:-312500}
    local scenario=${7:-reno}
    local directory_path="${8}"
    local ss_interval=$((delay/3))

    echo "h1 run_iperf_and_ss $duration $algorithm $bg_flows $delay $bandwidth $queue_size $ss_interval $scenario 0 $directory_path" | start_mininet $algorithm $delay $bandwidth $queue_size $bg_flows
}


# Starts Mininet and runs iperf for the specified duration with the specified congestion control algorithm and number of background flows.
# Also captures packet data using TShark.
# In addition, collects and saves socket statistics periodically that are used to produce a cwnd plot.
# Optional parameters for delay, bandwidth, and queue size can also be specified.
# If no parameters are provided, default values are used.
# Parameters:
# $1: Duration for iperf to run for in seconds (default: 600).
# $2: Congestion control algorithm to use (default: cubic).
# $3: Number of background flows to use (default: 0).
# $4: Delay to use in ms (default: 50).
# $5: Bandwidth to use in Mbit (default: 50).
# $6: Queue size to use (default: 312500).
# $7: Scenario to use (default: reno).
# $8: Model inference flag (default: 0).
# $9: Path to the file containing the packet loss prediction (default: "").
# $10: Directory path where the output file should be saved.
# $11: Toggle ECN flag (default: 1).
start_and_run_connection_and_collect_data() {
    local duration=${1:-600}
    local algorithm=${2:-cubic}
    local bg_flows=${3:-0}
    local delay=${4:-50}
    local bandwidth=${5:-50}
    local queue_size=${6:-312500}
    local scenario=${7:-reno}
    local model_inference=${8:-0}
    local prediction_file_path=${9:-""}
    local directory_path="${10}"
    local toggle_ecn="${11:-1}"
    local ss_interval=$((delay/3))

    if [ -n "$9" ] && [ -z "${11}" ]; then
        directory_path="$9"
        toggle_ecn="${10}"
        prediction_file_path=""
    else
        directory_path="${10}"
        toggle_ecn="${11}"
    fi

    local pcap_path="${directory_path}/tshark_data.pcap"

    echo "h1 create_pcap_file $pcap_path && capture_traffic_tshark $pcap_path & run_iperf_and_ss $duration $algorithm $bg_flows $delay $bandwidth $queue_size $ss_interval $scenario $model_inference $directory_path" | start_mininet $algorithm $delay $bandwidth $queue_size $bg_flows $toggle_ecn $prediction_file_path
}


# Runs iperf for the specified duration and captures socket statistics periodically with the specified interval for the specified duration.
# Parameters:
# $1: Duration for iperf to run for in seconds.
# $2: Congestion control algorithm to use.
# $3: Number of background flows to use.
# $4: Delay to use in ms.
# $5: Bandwidth to use in Mbit.
# $6: Queue size to use.
# $7: Interval at which to capture socket statistics.
# $8: Scenario to use (either "reno", "cubic", or "half").
# $9: Whether to write the ss data for prediction or not (either 0 or 1).
# $10: Directory path where the output file should be saved.
run_iperf_and_ss() {
    local duration=$1
    local cc_algorithm=$2
    local bg_flows=$3
    local delay=$4
    local bandwidth=$5
    local queue_size=$6
    local ss_interval=$7
    local scenario=$8
    local predict=$9
    local directory_path="${10}"

    # Start iperf and capture socket statistics with specified parameters.
    if [ $bg_flows -eq 0 ]; then
        iperf3 -c 10.2.2.100 --cport 5001 -p 5201 -t $duration -C $cc_algorithm &
        capture_ss_with_args_periodically $ss_interval $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $predict $directory_path
    elif [ $bg_flows -eq 1 ] && ([ $scenario == "half" ] || [ $scenario == "reno" ]); then
        # Start a single foreground and background flow using Reno.
        iperf3 -c 10.2.2.100 --cport 5001 -p 5201 -t $duration -C $cc_algorithm &
        iperf3 -c 10.2.2.100 --cport 5002 -p 5202 -t $duration -C reno &
        capture_ss_with_args_periodically $ss_interval $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $predict $directory_path
    elif [ $bg_flows -le 6 ] && ([ $scenario == "reno" ] || [ $scenario == "cubic" ]); then
        # Start a single foreground and multiple background flows where all background flows are using either Reno or Cubic.
        iperf3 -c 10.2.2.100 --cport 5001 -p 5201 -t $duration -C $cc_algorithm &
        for ((i=0;i<$bg_flows;i++)); do
            port=$((5002+i))
            s_port=$((5202+i))
            iperf3 -c 10.2.2.100 --cport $port -p $s_port -t $duration -C $scenario &
        done
        capture_ss_with_args_periodically $ss_interval $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $predict $directory_path
    elif [ $bg_flows -le 6 ] && [ $scenario == "half" ]; then
        # Start a single foreground and multiple background flows where half of the background flows use Reno and the other half Cubic.
        iperf3 -c 10.2.2.100 --cport 5001 -p 5201 -t $duration -C $cc_algorithm &
        for ((i=0;i<$bg_flows;i++)); do
            port=$((5002+i))
            s_port=$((5202+i))
            if [ $((i%2)) -eq 0 ]; then
                iperf3 -c 10.2.2.100 --cport $port -p $s_port -t $duration -C reno &
            else
                iperf3 -c 10.2.2.100 --cport $port -p $s_port -t $duration -C cubic &
            fi
        done
        capture_ss_with_args_periodically $ss_interval $duration $cc_algorithm $bg_flows $delay $bandwidth $queue_size $scenario $predict $directory_path
    fi
}


# Creates a .pcap file with the specified name and assigns the correct permissions.
# If no parameters are provided, a default file name is used.
# Parameters:
# $1: (optional) Name of the .pcap file (default: "output.pcap").
create_pcap_file() {
    local pcap_file_name=${1:-"./output/pcap/output.pcap"}

    touch "$pcap_file_name" && chmod 777 "$pcap_file_name"
}


# Call the create_pcap_file function with specific values for the arguments.
create_pcap_file_with_args() {
	create_pcap_file "./output/pcap/tshark_data.pcap"
}


# Captures traffic from the first Mininet host using tshark and writes it to the specified output file.
# Parameters:
# $1: Output file path where the traffic data will be saved.
capture_traffic_tshark() {
    local output_file=$1

    sudo tshark -i h1-r -f "tcp" -w "$output_file"
}


# Gets the number of TCP retransmissions and throughput from a given pcap file and writes stats to output file.
# Uses tshark to filter and calculate the TCP retransmissions and throughput.
# Parameters:
# $1: Path to the pcap file.
# $2: Congestion control algorithm.
# $3: Number of background flows.
# $4: Delay in ms.
# $5: Bandwidth in Mbit.
# $6: Queue size in packets.
# $7: Scenario (either "reno", "cubic", or "half").
# $8: Duration of the test (in seconds).
# $9: Model inference flag (either 0 or 1).
# $10: Classification threshold for model inference.
# $11: Directory path where the output file should be saved.
# $12: (Optional) Calculate metrics flag (default: false) - If true, calculates retransmissions and throughput.
get_metrics() {
    local pcap_path="$1"
    local congestion_algorithm="$2"
    local bg_flows="$3"
    local delay="$4"
    local bandwidth="$5"
    local queue_size="$6"
    local scenario="$7"
    local duration="$8"
    local model_inference="$9"
    local threshold="${10}"
    local directory_path="${11}"
    local calculate_metrics="${12:-false}"

    local output_file="${directory_path}/metrics.txt"

    echo "Extracting metrics and connection parameters from $pcap_path..."

    # Create the directory if it doesn't exist
    mkdir -p "$directory_path"

    echo "Congestion Control Algorithm: $congestion_algorithm" > "$output_file"
    echo "Background Flows: $bg_flows" >> "$output_file"
    echo "Scenario: $scenario" >> "$output_file"
    echo "Delay: $delay ms" >> "$output_file"
    echo "Bandwidth: $bandwidth Mbit" >> "$output_file"
    echo "Queue Size: $queue_size bytes" >> "$output_file"
    echo "Duration: $duration seconds" >> "$output_file"
    echo "Model inference: $model_inference" >> "$output_file"
    echo "Classification Threshold: $threshold" >> "$output_file"

    if [[ "$calculate_metrics" == "true" ]]; then
        echo "Getting the number of retransmissions..."
        local retransmissions=$(tshark -r "$pcap_path" -Y "tcp.analysis.retransmission" -T fields -e frame.number | wc -l)
        echo "Retransmissions: $retransmissions" >> "$output_file"
        echo "Done getting the number of retransmissions."

        # Extract total bytes transferred using tshark (excluding headers)
        echo "Calculating throughput..."
        local total_bytes=$(tshark -r "$pcap_path" -T fields -e tcp.len | awk '{sum+=$1} END {print sum}')

        # Calculate throughput in Mbit/s
        local throughput_mbps=$(bc <<< "scale=2; ($total_bytes*8)/(1000000*$duration)")

        echo "Throughput: $throughput_mbps Mbit/s" >> "$output_file"
        echo "Done calculating throughput."

    fi

    echo -e "" >> "$output_file"
    echo "Metrics and connection parameters have been extracted to $output_file."
}


# Capture traffic from first mininet host using tcpdump and write to given file.
capture_traffic_tcpdump() {
	sudo tcpdump -i s1-eth1 -f "src host 10.0.0.1 && tcp" -w "$1"
}


# Capture traffic from first mininet host using either tshark or tcpdump depending on passed argument and write to given file.
capture_traffic() {
	if [ $1 = "tshark" ]
	then
		capture_traffic_tshark "$2"
	else
		capture_traffic_tcpdump "$2"
	fi
}


# Call the capture_traffic function with specific values for the arguments.
capture_traffic_with_args() {
	capture_traffic "tshark" "./output/pcap/tshark_data.pcap"
}


# Extract the information from a given .pcap file into a given .txt file.
extract_pcap_info() {
	tshark -r "$1" -V > "$2"
}


# Call the extract_pcap_info function with specific values for the arguments.
extract_pcap_info_with_args() {
	extract_pcap_info "./output/pcap/tshark_data.pcap" "./output/text/tshark_data.txt"
}


# Use ss to capture socket statistics from the first Mininet host and append to given file.
# Parameters:
# $1: File to write socket statistics to.
capture_ss() {
	local file="$1"

	ss -i -o src 10.1.1.100:5001 dst 10.2.2.100:5201 >> "$file"
}


# Use ss to capture socket statistics from the first Mininet host and write to given file.
# Parameters:
# $1: File to write socket statistics to.
capture_ss_with_overwrite() {
	local file="$1"

	ss -i -o src 10.1.1.100:5001 dst 10.2.2.100:5201 > "$file"
}


# Call the capture_ss function every given milliseconds until the given seconds have elapsed.
# Parameters:
# $1: Interval at which to call capture_ss_with_args function in seconds.
# $2: Duration to run the loop in seconds.
# $3: Congestion control algorithm used.
# $4: Number of background flows.
# $5: Delay used.
# $6: Bandwidth used.
# $7: Queue size used.
# $8: Scenario used.
# $9: (optional) Flag to indicate whether to write to prediction file as well.
# $10: Directory path where the output file should be saved.
capture_ss_with_args_periodically() {
    local interval=$1
    local duration=$2
    local cc_algorithm=$3
    local bg_flows=$4
    local delay=$5
    local bandwidth=$6
    local queue_size=$7
    local scenario=$8
    local predict=${9:-0}
    local directory_path="${10}"

    local file_path="${directory_path}/ss_data.txt"
    local prediction_file_path="${directory_path}/ss_data_predict.txt"

    echo $file_path

    # Create directory if it doesn't exist.
    mkdir -p "$directory_path"

    # Change owner of directory if it already exists and add read, write, and execute permissions.
    chown -R maxvons "$directory_path"
    chmod -R u+rwx "$directory_path"

    # Delete file if it already exists.
    if [ -f "$file_path" ]
    then
        rm "$file_path"
    fi

    if [ -z "$interval" ]
    then
        echo "Please provide the interval in milliseconds."
        return 1
    fi

    # Set start time.
    start_time=$(date +%s)

    while :
    do
        capture_ss "$file_path"
        if [ "$predict" -eq 1 ]; then
            capture_ss_with_overwrite "$prediction_file_path"
        fi

        # Calculate elapsed time
        end_time=$(date +%s)
        elapsed_time=$((end_time - start_time))

        # Stop if elapsed time exceeds the specified duration.
        if [ "$elapsed_time" -ge "$duration" ]; then
            break
        fi
    done

    # Change owner.
    chown maxvons "$file_path"
    chmod u+rwx "$file_path"

    chown maxvons "$prediction_file_path"
    chmod u+rwx "$prediction_file_path"
}


# Watches a given file and dynamically enables or disables ECN based on the file's content.
# The function reads the content of the file, which should be either 1 (enable ECN) or 0 (disable ECN),
# and executes corresponding commands to adjust ECN settings.
# Parameters:
# $1: Path to the file that should be watched for changes.
# $2: Round-trip time delay in milliseconds.
toggle_ecn() {
    local input_file_path="$1"
    local delay="$2"
    local watch_interval=$((delay / 3))
    local prev_content=""

    while true; do
        local file_content=$(cat "$input_file_path")

        if [[ "$file_content" != "$prev_content" ]]; then
            # Clear previous rules.
            iptables -t mangle -F OUTPUT

            if [[ "$file_content" == "1" ]]; then
                # Enable ECN.
                iptables -t mangle -A POSTROUTING -p tcp -j TOS --set-tos 3
            elif [[ "$file_content" == "0" ]]; then
                # Disable ECN.
                iptables -t mangle -D POSTROUTING -p tcp -j TOS --set-tos 3
            fi

            # Update previous content.
            prev_content="$file_content"
        fi

        sleep $((watch_interval / 1000)).$((watch_interval % 1000))
    done
}


# Calculates the queue size in bytes based on the provided delay, bandwidth, and BDP multiplier.
# Parameters:
# $1: Round-trip time delay in milliseconds.
# $2: Bandwidth in Mbit/s.
# $3: Multiplier for the BDP to compute the queue size.
calculate_queue_size() {
    local delay=$1
    local bandwidth=$2
    local multiplier=$3

    # Calculate the queue size in bytes based on BDP multiplier
    LC_NUMERIC="en_US.UTF-8"
    local queue_size_bytes
    queue_size_bytes=$(echo "($bandwidth * 1000000 * $delay / 8000) * $multiplier" | bc)

    # Convert to integer
    queue_size_bytes=$(printf "%.0f" $queue_size_bytes)

    echo $queue_size_bytes
}
