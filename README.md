# How to run the data capture procedure

The entire data capture procedure has been configured to run automatically using the script called `data_capture.sh`. The script takes seven arguments: the duration in seconds for the data capture procedure, the congestion control algorithm to use, the number of background flows (between 0 and 6 inclusive), the delay in milliseconds, the bandwidth in Mbits, the queue size to use, and the scenario to run, where scenario refers to the congestion control algorithm the background flows are configured with.

Make sure to navigate to the correct directory before running the script: `masters-thesis/data_pipeline/data_capture`.

An example showing how to run the data capture procedure for 10 seconds using TCP Reno, one background flow, a delay of 50ms, a bandwidth of 50 Mbits, a queue size of 312500, and the default scenario of Reno for all background flows:

```bash
./data_capture.sh -d 10 -c reno -n 1 -l 50 -b 50 -q 312500 -s reno
```

If any of the arguments are omitted, the script will use the following default values:

- duration: 300
- cc_algorithm: cubic
- bg_flows: 0
- delay: 50
- bandwidth: 50
- queue_size: 312500
- scenario: reno

The script will prompt you for your sudo password before spawning a new terminal window and starting the different components of the data capture procedure. This is to ensure that the tools requiring sudo access can run automatically.

The output will be saved to the `output` directory, under the relevant subdirectories there.
