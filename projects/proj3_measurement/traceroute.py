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
			out = subprocess.check_output(['traceroute', '-a', '-q', str(num_packets), host])
			f.write("this is host: " + host + "\n")
			f.write("type= normal\n")
			f.write(out)
			f.write('\n')

def parse_traceroute(raw_traceroute_filename, output_filename):
	regex_normal = re.compile('(.*)\[(.*)\]\s+(.*)\s+\((.*)\)|^(\d+)*\s+(\*\s*[\*\s]*)')
	regex_server = re.compile('\s*(\d*)\s+(.*)\s?\((.*)\)\s?(\[AS\s?\d+\])?|(\d+)*\s+(\*\s*[\*\s]*)')
	num_regex = re.compile('(\d+)')
	asn_regex = re.compile('\[AS (\d+)\]')
	hostname = re.compile('this is host: (.*)')
	output_type = re.compile('type= (.*)')
	lines = [line.rstrip('\n') for line in open(raw_traceroute_filename)]
	t = lines[0]
	trace_out = {"timestamp" : t}
	i = 0
	normal = True
	for line in lines[1:]:
		if not line:
			continue
		out_type = output_type.findall(line)

		if out_type:
			if out_type[0] == "server":
				normal = False
			else:
				normal = True

		m = hostname.findall(line)
		if m:
			host = m[0]
			trace_out[host] = []
			print "host: " + host
			continue
		if normal:
			match = regex_normal.findall(line)
			if match:
				print match                                          
				seq_n, asn, name, ip, error_seq, error = match[0]
				num = num_regex.findall(seq_n)
				if num:
					i = int(num[0]) - 1
					trace_out[host].append([])
				if error:
					if error_seq:
						i = int(error_seq) - 1
						trace_out[host].append([])
					print i
					trace_out[host][i].append({'name': "None", "ip":"None", "ASN":"None"})
				else:
					asn_match = re.compile('AS(\d+)')
					a = asn_match.findall(asn)
					if '*' in asn or a[0] == '0':
						trace_out[host][i].append({'name':name, 'ip':ip, "ASN":"None"})
					else:
						trace_out[host][i].append({'name':name, 'ip':ip, "ASN":a[0]})
		else:
			match = regex_server.findall(line)
			if match:
				print match
				seq_n, name, ip, asn, error_seq, error = match[0]
				if seq_n:
					n = num_regex.findall(seq_n)
					i = int(n[0]) - 1
					trace_out[host].append([])
				if error:
					if error_seq:
						e = num_regex.findall(error_seq)
						i = int(e[0]) - 1
						trace_out[host].append([])
					print i
					trace_out[host][i].append({'name': "None", "ip":"None", "ASN":"None"})
				else:
					name = name.strip()
					if ip == "":
						ip = name
					a = asn_regex.findall(asn)
					print i
					if not a or a[0] == '0':
						trace_out[host][i].append({'name':name, 'ip':ip, "ASN":"None"})
					else:
						trace_out[host][i].append({'name':name, 'ip':ip, "ASN":a[0]})


	if not os.path.exists(output_filename):
		with open(output_filename, 'a') as f:
			json.dump(trace_out, f)
	else:
		with open(output_filename, 'a') as f:
			f.write('\n')
			json.dump(trace_out, f)

if __name__ == '__main__':
	# run_traceroute(['google.com', 'facebook.com', 'www.berkeley.edu', 'allspice.lcs.mit.edu', 'todayhumor.co.kr', 'www.city.kobe.lg.jp', 'www.vutbr.cz', 'zanvarsity.ac.tz'], 5, 'tr_a_raw.txt')
	# run_traceroute(['tpr-route-server.saix.net', 'route-server.ip-plus.net', 'route-views.oregon-ix.net', 'route-views.on.bb.telus.com'], 5, 'tr_b_raw.txt')
	# parse_traceroute('tr_a_raw.txt', 'tr_a.json')
	parse_traceroute('tr_b_raw.txt', 'tr_b.json')
	parse_traceroute('reverse_raw.txt', 'tr_b.json')



