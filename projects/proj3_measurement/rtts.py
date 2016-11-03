"""A python script that pings servers and records/plots the rtts and drop rate"""
import subprocess
from collections import defaultdict

""" Runs ping commands and generates json output
	hostnames: list of hosts to ping
	num_packets: number of packets to send to each host
	raw_ping_output_filename: name of file to output the raw ping results to
	aggregated_ping_output_filename: name of file to output the aggregated ping results to """

def run_ping(hostnames, num_packets, raw_ping_output_filename, aggregated_ping_output_filename):
	rtts = dict()
	for host in hostnames:
		# Ping host num_packets times
		output = subprocess.check_output(["ping", "-c", str(num_packets), host])
		# Go though the lines of output and write to raw_ping_output_filename
		# Timeouts should have rtt = -1
		lines = output.split('\n')[1:]
		rtts[host] = [-1] * num_packets
		for line in lines:
			print line
			if not line:
				break
			elif 'bytes from' not in line:
				continue
			else:
				index = int(line.split()[4].split('=')[1])
				rtts[host][index] = float(line.split()[6].split('=')[1])

		# Aggregate data is in the last 2 lines of output anyway,
		# so we can just use this instead of keeping track while we are going through the lines of output
	return rtts

def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
	return None


def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
	return None


if __name__ == '__main__':
	out = run_ping(['google.com'], 30, None, None)
	print len(out['google.com'])
	print out
