import json
import pprint
import re
import subprocess
import utils
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def run_dig(hostname_filename, output_filename, dns_query_server=None):
    with open(hostname_filename, 'r') as f:
        to_write = []
        for hostname in f.readlines():
            hostname = hostname.strip()
            print hostname
            for i in range(5):
                try:
                    host_dict = {
                        utils.NAME_KEY: hostname,
                        utils.SUCCESS_KEY: True,
                        utils.QUERIES_KEY: []
                    }
                    query = {utils.ANSWERS_KEY: []}
                    if not dns_query_server:
                        output = subprocess.check_output('dig +trace +nofail +tries=1 ' + hostname, shell=True)
                        answer_pattern = re.compile('(.*?\.)\s+(\d+)\s+IN\s+(\w+)\s+(.*)')
                        received_pattern = re.compile(';; Received \d+ bytes from .* in (\d+) ms')
                        for line in output.split('\n'):
                            if answer_pattern.match(line):
                                name, ttl, result_type, data = answer_pattern.findall(line)[0]
                                answer = {
                                    utils.QUERIED_NAME_KEY: name,
                                    utils.TTL_KEY: int(ttl),
                                    utils.TYPE_KEY: result_type,
                                    utils.ANSWER_DATA_KEY: data
                                }
                                query[utils.ANSWERS_KEY].append(answer)
                            elif received_pattern.match(line):
                                time = int(received_pattern.findall(line)[0])
                                query[utils.TIME_KEY] = time
                                host_dict[utils.QUERIES_KEY].append(query)
                                query = {utils.ANSWERS_KEY: []}
                    else:
                        output = subprocess.check_output('dig ' + hostname + ' @'  + dns_query_server, shell=True)
                        answer_pattern = re.compile(';; ANSWER SECTION:\n(.*)\s+(\d+)\s+IN\s+(\w+)\s+(.*)\n')
                        time_pattern = re.compile(';; Query time: (\d+) msec')
                        time = int(time_pattern.findall(output)[0])
                        for name, ttl, result_type, data in answer_pattern.findall(output):
                            answer = {
                                utils.QUERIED_NAME_KEY: name.strip(),
                                utils.TTL_KEY: int(ttl),
                                utils.TYPE_KEY: result_type,
                                utils.ANSWER_DATA_KEY: data
                            }
                            query[utils.ANSWERS_KEY].append(answer)
                        query[utils.TIME_KEY] = time
                        host_dict[utils.QUERIES_KEY].append(query)
                except subprocess.CalledProcessError:
                    host_dict = {
                        utils.NAME_KEY: hostname,
                        utils.SUCCESS_KEY: False
                    }
                to_write.append(host_dict)
    with open(output_filename, 'w') as f:
        json.dump(to_write, f)

def average(lst):
    return sum(lst) / float(len(lst))

def get_average_ttls(filename):
    with open(filename, 'r') as f:
        dig_results = json.load(f)
        all_root, all_tld, all_other, all_terminating = [], [], [], []
        for result in dig_results:
            if result[utils.SUCCESS_KEY]:
                query_number = 0
                root, tld, other, terminating = [], [], [], []
                for query in result[utils.QUERIES_KEY]:
                    if query_number == 0: # root
                        for answer in query[utils.ANSWERS_KEY]:
                            root.append(answer[utils.TTL_KEY])
                    elif query_number == 1: # tld
                        for answer in query[utils.ANSWERS_KEY]:
                            tld.append(answer[utils.TTL_KEY])
                    else: # either other or terminating
                        for answer in query[utils.ANSWERS_KEY]:
                            result_type = answer[utils.TYPE_KEY]
                            if result_type == 'NS':
                                other.append(answer[utils.TTL_KEY])
                            elif result_type == 'A' or result_type == 'CNAME':
                                terminating.append(answer[utils.TTL_KEY])
                    query_number += 1
                all_root.append(average(root))
                all_tld.append(average(tld))
                all_other.append(average(other))
                all_terminating.append(average(terminating))
        return map(average, [all_root, all_tld, all_other, all_terminating])

def get_total_and_final_times(filename):
    with open(filename, 'r') as f:
        dig_results = json.load(f)
        total_times, final_times = [], []
        for result in dig_results:
            if result[utils.SUCCESS_KEY]:
                total_time = 0
                for query in result[utils.QUERIES_KEY]:
                    time = query[utils.TIME_KEY]
                    total_time += time
                    for answer in query[utils.ANSWERS_KEY]:
                        result_type = answer[utils.TYPE_KEY]
                        if result_type == 'A' or result_type == 'CNAME':
                            final_times.append(time)
                            break
                total_times.append(total_time)
    return total_times, final_times

def get_average_times(filename):
    total_times, final_times = get_total_and_final_times(filename)
    return map(average, [total_times, final_times])

def generate_time_cdfs(json_filename, output_filename):
    total_times, final_times = map(sorted, get_total_and_final_times(json_filename))
    plt.step(total_times, np.linspace(0, 1, len(total_times)), label='Total time')
    plt.step(final_times, np.linspace(0, 1, len(final_times)), label='Final request time')
    plt.grid()
    plt.legend()
    plt.xlabel('Time (ms)')
    plt.ylabel('Cumulative Fraction')
    plt.title('CDF of DNS Times')
    plt.show()

def count_different_dns_responses(filename1, filename2):
    responses = defaultdict(set)
    with open(filename1, 'r') as f:
        dig_results = json.load(f)
        for result in dig_results:
            hostname = result[utils.NAME_KEY]
            if result[utils.SUCCESS_KEY]:
                for query in result[utils.QUERIES_KEY]:
                    for answer in query[utils.ANSWERS_KEY]:
                        result_type = answer[utils.TYPE_KEY]
                        if result_type == 'A' or result_type == 'CNAME':
                            data = answer[utils.ANSWER_DATA_KEY]
                            responses[hostname].add(data)
    count1 = 0
    for hostname in responses:
        if len(responses[hostname]) > 1:
            count1 += 1
    with open(filename2, 'r') as f:
        dig_results = json.load(f)
        for result in dig_results:
            hostname = result[utils.NAME_KEY]
            if result[utils.SUCCESS_KEY]:
                for query in result[utils.QUERIES_KEY]:
                    for answer in query[utils.ANSWERS_KEY]:
                        result_type = answer[utils.TYPE_KEY]
                        if result_type == 'A' or result_type == 'CNAME':
                            data = answer[utils.ANSWER_DATA_KEY]
                            responses[hostname].add(data)
    count2 = 0
    for hostname in responses:
        if len(responses[hostname]) > 1:
            count2 += 1
    return count1, count2

if __name__ == '__main__':
    # run_dig('alexa_top_100', 'test.json', '80.65.225.62')
    # run_dig('alexa_top_100', 'dns_output_4.json')
    # print get_average_ttls('dig_output.json')
    # print get_average_ttls('dig_output2.json')
    # print get_average_times('dns_output_1.json')
    # generate_time_cdfs('dns_output_1.json', None)
    # generate_time_cdfs('dns_output_2.json', None)
    # with open('dns_output_3.json', 'r') as f:
    #     d = json.load(f)
    #     pprint.pprint(d)
    print count_different_dns_responses('dns_output_3.json', 'dns_output_4.json')
    print count_different_dns_responses('dns_output_3.json', 'test.json')
    # print count_different_dns_responses('dns_output_3.json', 'test.json')
