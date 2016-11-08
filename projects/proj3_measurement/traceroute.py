import time
import subprocess
import re
import json
import os.path


def run_traceroute(hostnames, num_packets, output_filename):
	t = str(time.time())
	with open(output_filename, 'w') as f:
		f.write(t + '\n')
		
		for host in hostnames:
			host = host.strip()
			# trace_out[host] = []
			out = subprocess.check_output(['traceroute', '-a', '-q', str(num_packets), host])
			f.write("this is host: " + host + "\n")
			f.write(out)
			f.write('\n')

def parse_traceroute(raw_traceroute_filename, output_filename): 

	regex = re.compile('(.*)\[AS(\d+)\]\s+(.*)\s+\((.*)\)|(\d+)*\s+(\*\s*[\*\s]*)')
	hostname = re.compile('this is host: (.*)')
	lines = [line.rstrip('\n') for line in open(raw_traceroute_filename)]
	t = lines[0]
	trace_out = {"timestamp" : t}
	for line in lines[1:]:
		if not line:
			continue
		m = hostname.findall(line)
		if m:
			host = m[0]
			trace_out[host] = []
		else:
		#case where this is our own machine
			i = 0
			match = regex.findall(line)
			if match:
				# print match
				seq_n, asn, name, ip, error_seq, error = match[0]
				num_regex = re.compile('(\d+)')
				num = num_regex.findall(seq_n)
				if num:
					i = int(num[0]) - 1
					trace_out[host].append([])
				if error:
					if error_seq:
						i = int(error_seq) - 1
						trace_out[host].append([])
					trace_out[host][i].append({'name': "None", "ip":"None", "ASN":"None"})
				else:
					# print ("adding entry " + str(i))
					# print ("ASN: " + asn)
					trace_out[host][i].append({'name':name, 'ip':ip, "ASN":asn})
					
		#case where this is from the server


	print trace_out

	if not os.path.exists(output_filename):
		with open(output_filename, 'a') as f:
			json.dump(trace_out, f)
	else:
		with open(output_filename, 'a') as f:
			f.write('\n')
			json.dump(trace_out, f)
			

if __name__ == '__main__':
	# run_traceroute(['google.com', 'facebook.com', 'www.berkeley.edu', 'allspice.lcs.mit.edu', 'todayhumor.co.kr', 'www.city.kobe.lg.jp', 'www.vutbr.cz'], 2, 'tr_a.json')
	# 'zanvarsity.ac.tz'
	# run_traceroute(['tpr-route-server.saix.net', 'route-server.ip-plus.net', 'route-views.oregon-ix.net', 'route-server.eastern.allstream.com'], 5, 'tr_b.json')
	run_traceroute(['google.com'], 2, 'tr_raw.txt')
	parse_traceroute('tr_raw.txt', 'split_test.json')



