import wan_optimizer
import utils
from tcp_packet import Packet
from collections import defaultdict
import sys

class WanOptimizer(wan_optimizer.BaseWanOptimizer):
    """ WAN Optimizer that divides data into fixed-size blocks.
    This WAN optimizer should implement part 1 of project 4.
    """

    # Size of blocks to store, and send only the hash when the block has been
    # sent previously
    BLOCK_SIZE = 8000

    def __init__(self):
        wan_optimizer.BaseWanOptimizer.__init__(self)
        # Add any code that you like here (but do not add any constructor arguments).
        self.hashtable = dict()
        self.buffer = defaultdict(str)

    def receive(self, packet):
        """ Handles receiving a packet.
        Right now, this function simply forwards packets to clients (if a packet
        is destined to one of the directly connected clients), or otherwise sends
        packets across the WAN. You should change this function to implement the
        functionality described in part 1.  You are welcome to implement private
        helper fuctions that you call here. You should *not* be calling any functions
        or directly accessing any variables in the other middlebox on the other side of
        the WAN; this WAN optimizer should operate based only on its own local state
        and packets that have been received.
        """
        if packet.dest in self.address_to_port:
            # The packet is destined to one of the clients connected to this middlebox;
            # send the packet there.
            port = self.address_to_port[packet.dest]
            client = True
            # don't send hashes to clients
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            port = self.wan_port
            client = False
        if packet.is_raw_data:
            total_buffer = self.get_buffer(packet.src, packet.dest) + packet.payload
            self.set_buffer(packet.src, packet.dest, total_buffer)
            while len(total_buffer) >= self.BLOCK_SIZE:
                to_send = total_buffer[:self.BLOCK_SIZE]
                total_buffer = total_buffer[self.BLOCK_SIZE:]
                self.set_buffer(packet.src, packet.dest, total_buffer)
                hashed = utils.get_hash(to_send)
                if self.find_hash(hashed) and not client:
                    if self.get_buffer(packet.src, packet.dest):
                        hash_packet = Packet(packet.src, packet.dest, False, False, hashed)
                        self.send(hash_packet, port)
                    else:
                        hash_packet = Packet(packet.src, packet.dest, False, packet.is_fin, hashed)
                        self.send(hash_packet, port)
                        return
                else:
                    self.add_hash(hashed, to_send)
                    self.split_and_send(to_send, packet, port)
        else:
            to_send = self.find_hash(packet.payload)
            self.split_and_send(to_send, packet, port)
        if packet.is_fin:
            # self.split_and_send(self.get_buffer(packet.src, packet.dest), packet, port)
            # self.set_buffer(packet.src, packet.dest, '')
            curr_buffer = self.get_buffer(packet.src, packet.dest)
            print "in final case"
            print "buffer has %d bytes left" % (len(curr_buffer))
            if packet.is_raw_data and curr_buffer:
                end_hash = utils.get_hash(curr_buffer)
                if self.find_hash(end_hash):
                    print "sending hash: %s" % (end_hash)
                    hash_packet = Packet(packet.src, packet.dest, False, True, end_hash)
                    self.send(hash_packet, port)
                else:
                    self.add_hash(end_hash, curr_buffer)
                    print "sending raw data: %s" % (curr_buffer)
                    self.split_and_send(curr_buffer, packet, port)
            self.set_buffer(packet.src, packet.dest, '')

    def split_and_send(self, to_send, packet, dest):
        original_packet = packet
        while True:
            if len(to_send) <= utils.MAX_PACKET_SIZE:
                payload = to_send
                packet = Packet(packet.src, packet.dest, True, original_packet.is_fin, payload)
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
        self.buffer[(src, dest)] = s

    def get_buffer(self, src, dest):
        return self.buffer[(src, dest)]