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
            # self.send(packet, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            # self.send(packet, self.wan_port)
            port = self.wan_port
        if packet.is_raw_data: 
            # compute hash, check if seen before, send packet
            total_buffer = self.get_buffer(packet.src, packet.dest) + packet.payload
            curr_offset = self.get_curr_offset(packet.src, packet.dest)

            if len(total_buffer) < self.WINDOW_SIZE:
                block_hash = utils.get_hash(total_buffer)
                self.set_buffer(packet.src, packet.dest, '', 0)
                if self.find_hash(block_hash):
                    hash_packet = Packet(packet.src, packet.dest, False, packet.is_fin, block_hash)
                    print("Sending hash from %s to %s", str(packet.src), str(packet.dest))
                    self.send(hash_packet, port)
                else:
                    self.add_hash(block_hash, total_buffer)
                    print("Sending raw data from %s to %s", str(packet.src), str(packet.dest))
                    self.split_and_send(total_buffer, packet, port)
                #don't compute hash, just send
            else:
                end_range = curr_offset + self.WINDOW_SIZE 
                while end_range <= len(total_buffer):
                    delimiter_hash = utils.get_hash(total_buffer[curr_offset:end_range])
                    if utils.get_last_n_bits(delimiter_hash, self.BITSTRING_LENGTH) == self.GLOBAL_MATCH_BITSTRING:
                        to_send = total_buffer[:end_range]
                        block_hash = utils.get_hash(to_send)
                        #set the buffer, and reset curr_offset to 0
                        self.set_buffer(packet.src, packet.dest, total_buffer[end_range:], 0)
                        if self.find_hash(block_hash):
                            if self.get_buffer(packet.src, packet.dest):
                                hash_packet = Packet(packet.src, packet.dest, False, False, block_hash)
                                print("Sending hash from %s to %s", str(packet.src), str(packet.dest))
                                self.send(hash_packet, port)
                            else:
                                hash_packet = Packet(packet.src, packet.dest, False, packet.is_fin, block_hash)
                                if packet.is_fin:
                                    print("Sending raw data + fin from %s to %s", str(packet.src), str(packet.dest))
                                else:
                                    print("Sending raw data from %s to %s", str(packet.src), str(packet.dest))
                                self.send(hash_packet, port)
                                return
                        else:
                            #add to hashtable
                            self.add_hash(block_hash, to_send)
                            #send raw data
                            print("Sending raw data from %s to %s", str(packet.src), str(packet.dest))
                            self.split_and_send(to_send, packet, port)
                        break
                    else:
                        curr_offset += 1
                        end_range += 1
                        self.set_buffer(packet.src, packet.dest, total_buffer, curr_offset)
                #if no delimiter is found, store the entire buffer so far and update the current offset
        else:
            to_send = self.find_hash(packet.payload)
            print("Sending raw data from %s to %s", str(packet.src), str(packet.dest))
            self.split_and_send(to_send, packet, port)
        if packet.is_fin:
            print("Sending fin from %s to %s", str(packet.src), str(packet.dest))
            self.split_and_send(self.get_buffer(packet.src, packet.dest), packet, port)
            self.set_buffer(packet.src, packet.dest, '', 0)



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

    def set_buffer(self, src, dest, s, offset):
        self.buffer[(src, dest)] = [s, offset]

    def get_buffer(self, src, dest):
        return self.buffer[(src, dest)][0]

    def get_curr_offset(self, src, dest):
        return self.buffer[(src, dest)][1]

