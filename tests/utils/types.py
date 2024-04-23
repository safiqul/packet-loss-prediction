import enum


class Feature(enum.Enum):
    """Enum for the supported features."""

    CWND = "cwnd"
    SSTHRESH = "ssthresh"
    EXPIRE_TIME = "expire_time"
    RETRANS = "retrans"
    RTO = "rto"
    RTT = "rtt"
    RTT_VAR = "rtt_var"
    LAST_SEND = "last_send"
    PACING_RATE = "pacing_rate"


class Metric(enum.Enum):
    """Enum for the different metrics."""

    THROUGHPUT = "throughput"
    RETRANSMISSIONS = "retransmissions"
