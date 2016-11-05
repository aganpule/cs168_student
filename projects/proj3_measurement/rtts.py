"""A python script that pings servers and records/plots the rtts and drop rate"""
import subprocess
import re
from numpy import median

""" Runs ping commands and generates json output
	hostnames: list of hosts to ping
	num_packets: number of packets to send to each host
	raw_ping_output_filename: name of file to output the raw ping results to
	aggregated_ping_output_filename: name of file to output the aggregated ping results to """

def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	raw_pings, aggregate_pings = dict(), dict()
	for host in hostnames:
		# Ping host num_packets times
		host = host.strip()
		print host
		output = subprocess.check_output(["ping", "-c", str(num_packets), host])
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
			'max_rtt': max(successes),
			'median_rtt': median(successes)
		}
	return raw_pings, aggregate_pings

def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
	return None


def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
	return None


if __name__ == '__main__':
	with open('alexa_top_100', 'r') as f:
		raw_pings, aggregate_pings = run_ping(f.readlines(), 1, None, None)
	print raw_pings
	print aggregate_pings
