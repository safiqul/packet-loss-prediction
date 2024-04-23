from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink

from time import sleep, time
from argparse import ArgumentParser


def init_argparse() -> ArgumentParser:
    """Initializes and returns ArgumentParser to easily handle command line arguments.

    Returns:
        The initialized ArgumentParser.

    """

    parser = ArgumentParser(
        description="Start mininet virtual network with custom options"
    )

    parser.add_argument(
        "-b",
        "--bandwidth",
        type=int,
        required=True,
        help="Connection bandwidth (integer)",
    )

    parser.add_argument(
        "-d",
        "--delay",
        type=str,
        required=True,
        help="Connection delay (string, e.g. '10ms')",
    )

    parser.add_argument("-l", "--loss", type=int, default=0, help="Loss rate (integer)")

    parser.add_argument(
        "-q", "--queue", type=int, default=10, help="Max queue size (integer)"
    )

    return parser


class SingleSwitchTopo(Topo):
    """A class describing a topology of a single switch connected to two hosts."""

    def __init__(self, bandwidth=None, delay=None, loss=None, maxq=None):
        self.bandwidth = bandwidth
        self.delay = delay
        self.loss = loss
        self.maxq = maxq
        super(SingleSwitchTopo, self).__init__()

    def build(self):
        switch = self.addSwitch("s1")

        host1 = self.addHost("h1")
        host2 = self.addHost("h2")

        # Add a link between the switch and each host.
        self.addLink(
            host1,
            switch,
            bw=self.bandwidth,
            delay=self.delay,
            loss=self.loss,
            max_queue_size=self.maxq,
        )
        self.addLink(
            host2,
            switch,
            bw=self.bandwidth,
            delay=self.delay,
            loss=self.loss,
            max_queue_size=self.maxq,
        )


def main():
    try:
        parser = init_argparse()
        args = parser.parse_args()
    except Exception as e:
        print(f"Error when parsing args: {e}")
        raise SystemExit()

    topo = SingleSwitchTopo(
        bandwidth=args.bandwidth, delay=args.delay, loss=args.loss, maxq=args.queue
    )

    net = Mininet(topo=topo, link=TCLink)

    net.interact()


if __name__ == "__main__":
    main()
