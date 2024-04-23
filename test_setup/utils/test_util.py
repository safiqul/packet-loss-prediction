import unittest
import util as utils


class TestUtilFunctions(unittest.TestCase):
    def test_calculate_queue_size(self):
        self.assertEqual(utils.calculate_queue_size(50, 100, 1), 625000)
        self.assertEqual(utils.calculate_queue_size(50, 100, 0.5), 312500)
        self.assertEqual(utils.calculate_queue_size(50, 50, 1), 312500)

    def test_get_cc_algo(self):
        ss_data_reno = [
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack ecn reno wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036"""
        ]
        ss_data_cubic = [
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack ecn cubic wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036"""
        ]
        ss_data_without_cc_algo = [
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack ecn wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036"""
        ]
        ss_data_reno_in_second_measurement = [
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack ecn wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036""",
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack ecn reno wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036""",
        ]
        self.assertEqual(utils.get_cc_algo(ss_data_reno), "reno")
        self.assertEqual(utils.get_cc_algo(ss_data_cubic), "cubic")
        self.assertEqual(utils.get_cc_algo(ss_data_without_cc_algo), "")
        self.assertEqual(utils.get_cc_algo(ss_data_reno_in_second_measurement), "reno")

    def test_get_cwnd_values(self):
        ss_data = [
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack reno wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:669 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036""",
            """tcp   ESTAB 0      5655000    10.1.1.100:5001   10.2.2.100:5201 timer:(on,300ms,0)
	    ts sack reno wscale:9,9 rto:300 rtt:99.413/0.261 mss:1448 pmtu:1500 rcvmss:536 advmss:1448 cwnd:550 ssthresh:412 bytes_sent:2441365 bytes_retrans:70952 bytes_acked:1180158 segs_out:1689 segs_in:829 data_segs_out:1687 send 78Mbps lastrcv:556 pacing_rate 115Mbps delivery_rate 47.8Mbps delivered:918 busy:504ms rwnd_limited:48ms(9.5%) unacked:822 retrans:49/49 lost:101 sacked:101 rcv_space:14480 rcv_ssthresh:42242 notsent:4464744 minrtt:50.036""",
        ]
        self.assertEqual(utils.get_cwnd_values(ss_data), [669, 550])


if __name__ == "__main__":
    unittest.main()
