import argparse
import sys

from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import Node
from mininet.net import Mininet
from argparse import BooleanOptionalAction


class LinuxRouter(Node):
    """A custom router class that can be used to create a router node in Mininet."""

    def __init__(self, name, **params):
        """Initializes the router.

        Args:
            name: The name of the node.
            cc_algorithm: The congestion control algorithm to use.
            delay: The delay to use.
            bandwidth: The bandwidth to use.
            queue_size: The queue size to use.
        """

        super(LinuxRouter, self).__init__(name, **params)
        connection_params = params["params"]
        self.cc_algorithm = connection_params["cc_algorithm"]
        self.delay = connection_params["delay"]
        self.bandwidth = connection_params["bandwidth"]
        self.queue_size = connection_params["queue_size"]
        self.model_inference = connection_params["model_inference"]
        self.input_file = connection_params["input_file"]

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd("sysctl net.ipv4.ip_forward=1")
        self.cmd("sudo tc qdisc del dev r-h2 root")
        self.cmd(
            f"sudo tc qdisc add dev r-h2 root handle 2: netem delay {self.delay}ms"
        )
        self.cmd("sudo tc qdisc add dev r-h2 parent 2: handle 3: htb default 10")
        self.cmd(
            f"sudo tc class add dev r-h2 parent 3: classid 10 htb rate {self.bandwidth}Mbit"
        )
        self.cmd(
            f"sudo tc qdisc add dev r-h2 parent 3:10 handle 11: bfifo limit {self.queue_size}"
        )
        self.cmd(f"sudo sysctl -w net.ipv4.tcp_congestion_control={self.cc_algorithm}")
        self.cmd("sudo sysctl -w net.ipv4.tcp_window_scaling=1")
        self.cmd("sudo ethtool -K r-h1 tso off")
        self.cmd("sudo ethtool -K r-h2 tso off")

        if self.model_inference:
            self.cmd("source bash_functions.sh")
            print("The value of the input file variable is:", self.input_file)
            self.cmd(f"toggle_ecn {self.input_file} {self.delay} &")

    def terminate(self):
        self.cmd("sysctl net.ipv4.ip_forward=0")
        super(LinuxRouter, self).terminate()


class Receiver(Node):
    """A custom receiver node that uses the specified congestion control algorithm.

    The receiver node is also responsible for starting the required amount of iperf3 servers needed for the background flows.
    """

    def __init__(self, name, **params):
        """Initializes the receiver.

        Args:
            name: The name of the node.
            cc_algorithm: The congestion control algorithm to use.
            background_flows: The number of background flows to use.
        """
        super(Receiver, self).__init__(name, **params)
        connection_params = params["params"]
        self.cc_algorithm = connection_params["cc_algorithm"]
        self.background_flows = connection_params["background_flows"]

    def config(self, **params):
        super(Receiver, self).config(**params)

        # Start the required amount of iperf3 servers.
        base_port = 5201
        for server in range(self.background_flows + 1):
            self.cmd(f"iperf3 -s -p {base_port + server} -D")

        self.cmd(f"sudo sysctl -w net.ipv4.tcp_congestion_control={self.cc_algorithm}")
        self.cmd("sudo sysctl -w net.ipv4.tcp_window_scaling=1")
        self.cmd("sudo ethtool -K h2-r tso off")
        self.cmd("sudo sysctl -w net.ipv4.tcp_ecn=1")

    def terminate(self):
        super(Receiver, self).terminate()


class Sender(Node):
    """A custom sender node that uses a specific congestion control algorithm."""

    def __init__(self, name, **params):
        """Initializes the sender.

        Args:
            name: The name of the node.
            cc_algorithm: The congestion control algorithm to use.
        """

        super(Sender, self).__init__(name, **params)
        connection_params = params["params"]
        self.cc_algorithm = connection_params["cc_algorithm"]

    def config(self, **params):
        super(Sender, self).config(**params)
        self.cmd("source bash_functions.sh")
        self.cmd(f"sudo sysctl -w net.ipv4.tcp_congestion_control={self.cc_algorithm}")
        self.cmd("sudo sysctl -w net.ipv4.tcp_window_scaling=1")
        self.cmd("sudo ethtool -K h1-r tso off")
        self.cmd("sudo sysctl -w net.ipv4.tcp_ecn=1")

    def terminate(self):
        super(Sender, self).terminate()


class MyTopo(Topo):
    def __init__(
        self,
        cc_algorithm: str,
        delay: int,
        bandwidth: int,
        queue_size: int,
        background_flows: int,
        model_inference: bool,
        input_file: str,
    ):
        """Create custom topology with given bandwidth, delay, queue size and congestion control algorithm.

        Args:
            cc_algorithm: congestion control algorithm
            delay: delay
            bandwidth: bandwidth
            queue_size: queue size
            background_flows: number of background flows
            model_inference: if model inference should be turned on or not
            input_file: path to the file that contains the output from the prediction
        """

        Topo.__init__(self)

        # Add hosts and router
        r = self.addHost(
            "r",
            ip="10.1.1.1/24",
            cls=LinuxRouter,
            params={
                "cc_algorithm": cc_algorithm,
                "delay": delay,
                "bandwidth": bandwidth,
                "queue_size": queue_size,
                "model_inference": model_inference,
                "input_file": input_file,
            },
        )

        h1 = self.addHost(
            "h1",
            ip="10.1.1.100/24",
            defaultRoute="via 10.1.1.1",
            cls=Sender,
            params={"cc_algorithm": cc_algorithm},
        )

        h2 = self.addHost(
            "h2",
            ip="10.2.2.100/24",
            defaultRoute="via 10.2.2.1",
            cls=Receiver,
            params={"cc_algorithm": cc_algorithm, "background_flows": background_flows},
        )

        # Add links
        self.addLink(h1, r, intfName1="h1-r", intfName2="r-h1", cls=TCLink)
        self.addLink(
            h2,
            r,
            intfName1="h2-r",
            intfName2="r-h2",
            params2={"ip": "10.2.2.1/24"},
            cls=TCLink,
        )


def init_argparse() -> argparse.ArgumentParser:
    """Initialize the argument parser.

    Returns:
        The argument parser.
    """

    parser = argparse.ArgumentParser(
        description="Run a custom topology with the specified bandwidth, delay, queue size, and congestion control algorithm."
    )
    parser.add_argument(
        "-a",
        "--algorithm",
        type=str,
        default="cubic",
        help="The congestion control algorithm to use.",
    )
    parser.add_argument("-d", "--delay", type=int, default=50, help="The delay to use.")
    parser.add_argument(
        "-b", "--bandwidth", type=int, default=50, help="The bandwidth to use."
    )
    parser.add_argument(
        "-q", "--queue_size", type=int, default=312500, help="The queue size to use."
    )
    parser.add_argument(
        "-f",
        "--background_flows",
        type=int,
        default=0,
        help="The number of background flows to use.",
    )
    parser.add_argument(
        "--model_inference",
        metavar="MODEL_INFERENCE",
        type=bool,
        action=BooleanOptionalAction,
        default=False,
        help="If model inference should be turned on or not.",
    )
    parser.add_argument(
        "-i",
        "--input_file",
        metavar="INPUT_FILE",
        type=str,
        help="Path to the file that contains the output from the prediction.",
        required="--model_inference" in sys.argv,
    )

    return parser


def main():
    parser = init_argparse()
    args = parser.parse_args()

    print("Algorithm: {}".format(args.algorithm))
    print("Delay: {}".format(args.delay))
    print("Bandwidth: {}".format(args.bandwidth))
    print("Queue size: {}".format(args.queue_size))
    print("Background flows: {}".format(args.background_flows))
    print("Model inference: {}".format(args.model_inference))
    print("Input file: {}".format(args.input_file))

    topo = MyTopo(
        args.algorithm,
        args.delay,
        args.bandwidth,
        args.queue_size,
        args.background_flows,
        args.model_inference,
        args.input_file,
    )
    net = Mininet(topo=topo, link=TCLink, controller=None)
    net.start()
    net.interact()


if __name__ == "__main__":
    main()
