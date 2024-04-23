from scapy.all import rdpcap, TCP, IP
from collections import defaultdict

from argparse import ArgumentParser


def init_argparse() -> ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The initialized argument parser.
    """
    parser = ArgumentParser(
        usage="python %(prog)s -i <input_file> -o <output_file> -d <duration> -s <src_ip>",
        description="Parse a pcap file and calculate the number of retransmissions and throughput.",
    )

    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=str,
        required=True,
        help="Path to the pcap file that should be parsed",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        metavar="OUTPUT_PATH",
        type=str,
        required=True,
        help="Path to where the output should be saved",
    )
    parser.add_argument(
        "-d",
        "--duration",
        metavar="DURATION",
        type=int,
        required=True,
        help="Duration that the measurement was running for in seconds",
    )
    parser.add_argument(
        "-s",
        "--src_ip",
        metavar="SRC_IP",
        type=str,
        required=True,
        help="IP of the sender",
    )

    return parser


def filter_retransmissions(packets: list) -> list:
    """Filter out all retransmissions from the packets.

    Args:
        packets: List of packets that should be filtered.

    Returns:
        The filtered list of packets without retransmissions
    """
    packets_without_retransmissions = []
    seqs = defaultdict(int)
    for packet in packets:
        if TCP in packet:
            seq = packet[TCP].seq
            seqs[seq] += 1
            if seqs[seq] == 1:  # Only add the packet if it is not a retransmission
                packets_without_retransmissions.append(packet)

    return packets_without_retransmissions


def filter_packets_by_timestamp(packets, seconds_to_skip: int) -> list:
    """Filter the packets to only include packets that are sent after the
    specified number of seconds.

    Args:
        packets: List of packets that should be filtered.
        seconds_to_skip: Number of seconds to skip.

    Returns:
        The filtered list of packets.
    """
    start_time = packets[0].time
    filtered_packets = [
        pkt for pkt in packets if pkt.time - start_time > seconds_to_skip
    ]

    return filtered_packets


def filter_packets_by_src(packets, src_ip: str) -> list:
    """Filter the packets to only include packets that are sent from the
    specified source IP.

    Args:
        packets: List of packets that should be filtered.
        src_ip: Source IP.

    Returns:
        The filtered list of packets.
    """
    return [pkt for pkt in packets if pkt.haslayer(IP) and pkt[IP].src == src_ip]


def get_retransmissions(packets) -> int:
    """Calculate the number of retransmissions in the pcap file.

    Args:
        packets: List of packets that should be included in the calculation.

    Returns:
        The number of retransmissions.
    """
    seq_numbers = defaultdict(int)
    retransmissions = 0

    for packet in packets:
        if TCP in packet:
            seq = packet[TCP].seq
            seq_numbers[seq] += 1
            if seq_numbers[seq] > 1:
                retransmissions += 1

    return retransmissions


def get_throughput(packets: list, duration: int) -> float:
    """Calculate the throughput in Mbps.

    Args:
        packets: List of packets that should be included in the calculation.
        duration: The duration of the measurement in seconds.

    Returns:
        The throughput in Mbps.
    """
    total_bytes = sum(len(packet[TCP].payload) for packet in packets if TCP in packet)
    throughput_mbps = (total_bytes * 8) / (1000000 * duration)

    return throughput_mbps


def get_metrics(
    input_file_path: str, output_file_path: str, duration: int, src_ip: str
):
    """Calculate the metrics for the pcap file.
    The pcap file is loaded using scapy and the retransmissions and throughput
    are calculated and appended to the output file.

    Args:
        input_file_path: Path to the pcap file that should be parsed.
        output_file_path: Path to where the output should be saved.
        duration: The duration of the measurement in seconds.
        src_ip: Source IP.
    """
    print("Reading the pcap file...")
    packets = rdpcap(input_file_path)

    print("Filtering the packets to only include packets sent from the sender...")
    packets = filter_packets_by_src(packets, src_ip)

    print("Filtering out retransmissions...")
    packets_without_retransmissions = filter_retransmissions(packets)

    print("Calculating the throughput...")
    throughput_mbps = get_throughput(packets_without_retransmissions, duration)

    print("Filtering the packets to only include packets sent after 1 second...")
    packets_after_slow_start_peak = filter_packets_by_timestamp(
        packets, 1
    )  # TODO: Keep this in mind

    print("Calculating the number of retransmissions...")
    retransmissions = get_retransmissions(packets_after_slow_start_peak)

    with open(output_file_path, "a") as output_file:
        output_file.write(f"Retransmissions: {retransmissions}\n")
        output_file.write(f"Throughput: {round(throughput_mbps, 2)}Mbps\n")


def main():
    parser = init_argparse()
    args = parser.parse_args()

    get_metrics(args.input_file, args.output_path, args.duration, args.src_ip)


main()
