"""A python script that pings servers and records/plots the rtts and drop rate"""
import subprocess
import re
from numpy import median
import json
import pprint

def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	raw_pings, aggregate_pings = dict(), dict()
	for host in hostnames:
		host = host.strip()
		raw_pings[host] = [-1.0] * num_packets
		print host
		try:
			output = subprocess.check_output(["ping", "-c", str(num_packets), host])
			p = re.compile('\d+ bytes from \d+\.\d+\.\d+\.\d+: icmp_seq=(\d+) ttl=\d+ time=(\d+\.\d+) ms')
			pings = p.findall(output)
			successes = []
			for seq_no, time in pings:
				raw_pings[host][int(seq_no)] = float(time)
				successes.append(float(time))
			raw_pings[host] = sorted(raw_pings[host])
			aggregate_pings[host] = {
				'drop_rate': 100 * (num_packets - len(successes)) / float(num_packets),
				'max_rtt': max(successes) if successes else -1.0,
				'median_rtt': median(successes) if successes else -1.0
			}
		except subprocess.CalledProcessError:
			aggregate_pings[host] = {
				'drop_rate': 100.0,
				'max_rtt': -1.0,
				'median_rtt': -1.0
			}
	with open('output/' + raw_ping_output_filename, 'w') as f:
		json.dump(raw_pings, f)
	with open('output/' + aggregated_ping_output_filename, 'w') as f:
		json.dump(aggregate_pings, f)

def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
	with open('output/' + agg_ping_results_filename, 'r') as f:
		aggregate_pings = json.load(f)
		medians = sorted([aggregate_pings[site]['median_rtt'] for site in aggregate_pings])
		pprint.pprint(medians)
		print sum([1 if n == -1.0 else 0 for n in medians])

def find_num_no_response():
	with open('output/rtt_a_agg.json', 'r') as f:
		aggregate_pings = json.load(f)
		return sum([1 if aggregate_pings[site]['median_rtt'] == -1.0 else 0 for site in aggregate_pings])

def find_num_at_least_one_failure():
	with open('output/rtt_a_raw.json', 'r') as f:
		raw_pings = json.load(f)
		return sum([1 if -1.0 in raw_pings[site] else 0 for site in raw_pings])

def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
	with open('output/' + raw_ping_results_filename, 'r') as f:
		raw_pings = json.load(f)


if __name__ == '__main__':
	# with open('alexa_top_100', 'r') as f:
	# 	run_ping(f.readlines(), 10, 'rtt_a_raw.json', 'rtt_a_agg.json')
		# run_ping(['google.com', 'todayhumor.co.kr', 'zanvarsity.ac.tz', 'taobao.com'], 500, 'rtt_b_raw.json', 'rtt_b_agg.json')
	# plot_median_rtt_cdf('rtt_a_agg.json', None)
