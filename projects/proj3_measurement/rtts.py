"""A python script that pings servers and records/plots the rtts and drop rate"""
import subprocess
import re
from numpy import median
import json

""" Runs ping commands and generates json output
	hostnames: list of hosts to ping
	num_packets: number of packets to send to each host
	raw_ping_output_filename: name of file to output the raw ping results to
	aggregated_ping_output_filename: name of file to output the aggregated ping results to """

def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	raw_pings, aggregate_pings = dict(), dict()
	for host in hostnames:
		host = host.strip()
		print host
		try:
			output = subprocess.check_output(["ping", "-c", str(num_packets + 1), host])
			p = re.compile('\d+ bytes from \d+\.\d+\.\d+\.\d+: icmp_seq=(\d+) ttl=\d+ time=(\d+\.\d+) ms')
			raw_pings[host] = [-1.0] * num_packets
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

	return None


def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
	return None


if __name__ == '__main__':
	with open('alexa_top_100', 'r') as f:
		# run_ping(f.readlines(), 10, 'rtt_a_raw.json', 'rtt_a_agg.json')
		run_ping(['google.com', 'todayhumor.co.kr', 'zanvarsity.ac.tz', 'taobao.com'], 500, 'rtt_b_raw.json', 'rtt_b_agg.json')

