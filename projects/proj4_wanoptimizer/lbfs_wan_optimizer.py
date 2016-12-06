import wan_optimizer
import utils
from tcp_packet import Packet
from collections import defaultdict

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into variable-sized
    blocks based on the contents of the file.
    This WAN optimizer should implement part 2 of project 4.
    """

    # The string of bits to compare the lower order 13 bits of hash to
    GLOBAL_MATCH_BITSTRING = '0111011001010'
    WINDOW_SIZE = 48
    BITSTRING_LENGTH = 13

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).
        self.hashtable = dict()
        self.buffer = defaultdict(lambda: ['', 0])

    def receive(self, packet):
        """ Handles receiving a packet.
        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 2.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            port = self.address_to_port[packet.dest]
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            port = self.wan_port
        if packet.is_raw_data:
            total_buffer = self.get_buffer(packet.src, packet.dest) + packet.payload
            curr_offset = self.get_curr_offset(packet.src, packet.dest)
            self.set_buffer(packet.src, packet.dest, total_buffer)
            end_range = curr_offset + self.WINDOW_SIZE
            while end_range <= len(total_buffer):
                delimiter_hash = utils.get_hash(total_buffer[curr_offset:end_range])
                if utils.get_last_n_bits(delimiter_hash, self.BITSTRING_LENGTH) == self.GLOBAL_MATCH_BITSTRING:
                    to_send = total_buffer[:end_range]
                    total_buffer = total_buffer[end_range:]
                    self.set_buffer(packet.src, packet.dest, total_buffer)
                    self.set_offset(packet.src, packet.dest, 0)
                    curr_offset = 0
                    end_range = self.WINDOW_SIZE
                    block_hash = utils.get_hash(to_send)
                    if self.find_hash(block_hash):
                        hash_packet = Packet(packet.src, packet.dest, False, False, block_hash)
                        self.send(hash_packet, port)
                    else:
                        self.add_hash(block_hash, to_send)
                        self.split_and_send(to_send, packet, port)
                else:
                    curr_offset += 1
                    end_range += 1
                    self.set_offset(packet.src, packet.dest, curr_offset)
        else:
            to_send = self.find_hash(packet.payload)
            self.split_and_send(to_send, packet, port)
        if packet.is_fin:
            curr_buffer = self.get_buffer(packet.src, packet.dest)
            if packet.is_raw_data and curr_buffer:
                end_hash = utils.get_hash(curr_buffer)
                if self.find_hash(end_hash):
                    hash_packet = Packet(packet.src, packet.dest, False, False, end_hash)
                    self.send(hash_packet, port)
                else:
                    self.add_hash(end_hash, curr_buffer)
                    self.split_and_send(curr_buffer, packet, port)
            fin_packet = Packet(packet.src, packet.dest, True, True, '')
            self.send(fin_packet, port)
            self.set_buffer(packet.src, packet.dest, '')
            self.set_offset(packet.src, packet.dest, 0)

    def split_and_send(self, to_send, packet, dest):
        while True:
            if len(to_send) <= utils.MAX_PACKET_SIZE:
                payload = to_send
                packet = Packet(packet.src, packet.dest, True, False, payload)
                self.send(packet, dest)
                return
            else:
                payload = to_send[:utils.MAX_PACKET_SIZE]
                packet = Packet(packet.src, packet.dest, True, False, payload)
                self.send(packet, dest)
                to_send = to_send[utils.MAX_PACKET_SIZE:]

    def find_hash(self, hashed):
        if hashed in self.hashtable:
            return self.hashtable[hashed]

    def add_hash(self, hashed, raw_data):
        self.hashtable[hashed] = raw_data

    def set_buffer(self, src, dest, s):
        self.buffer[(src, dest)][0] = s

    def set_offset(self, src, dest, offset):
        self.buffer[(src, dest)][1] = offset

    def get_buffer(self, src, dest):
        return self.buffer[(src, dest)][0]

    def get_curr_offset(self, src, dest):
        return self.buffer[(src, dest)][1]
