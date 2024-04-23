clean:
	rm -f ./output/text/tshark_data.txt ./output/text/*.txt
	rm -f ./output/pcap/tshark_data.pcap
	
remove_reno_file:
	rm -f ./output/text/ss_data_reno.txt
	
remove_cubic_file:
	rm -f ./output/text/ss_data_cubic.txt
	
remove_bbr_file:
	rm -f ./output/text/ss_data_bbr.txt
	
capture:
	./data_capture.sh 10
	
format:
	autopep8 --in-place --aggressive --aggressive mn_topo.py
	autopep8 --in-place --aggressive --aggressive mn_script_old.py
	
start_mininet:
	sudo python3 mn_topo.py
	
