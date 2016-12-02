import wan_optimizer
import utils
from tcp_packet import Packet

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
        self.hash = {}
        self.buffer = ""
        return

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
            if packet.is_raw_data:
                self.send(packet, self.address_to_port[packet.dest])
            else:
                to_send = self.hash[packet.payload]
                self.split_and_send(packet, to_send, self.address_to_port[packet.dest])
        else:
            # The packet must be destined to a host connected to the other middlebox
            # so send it across the WAN.
            if packet.is_raw_data:
                total_buffer = self.buffer + packet.payload
                if len(total_buffer) >= self.BLOCK_SIZE:
                    to_send = total_buffer[:self.BLOCK_SIZE]
                    self.buffer = total_buffer[self.BLOCK_SIZE:]
                    hashed = utils.get_hash(to_send)
                    if hashed in self.hash:
                        hash_packet = Packet(packet.src, packet.dest, False, False, hashed)
                        self.send(hash_packet, self.wan_port)
                    else:
                        self.hash[hashed] = to_send
                        self.split_and_send(to_send, packet, self.wan_port)
                else:
                    self.buffer = total_buffer
            if packet.is_fin:
                # packet = Packet(packet.src, packet.dest, True, True, '')
                # self.send(packet, self.wan_port)
                self.split_and_send(self.buffer, packet, self.wan_port)
                self.buffer = ''

    def split_and_send(self, to_send, packet, dest):
        original_packet = packet
        while True:
            if len(to_send) < utils.MAX_PACKET_SIZE:
                payload = to_send
                packet = Packet(packet.src, packet.dest, True, original_packet.is_fin, payload)
                self.send(packet, dest)
                return
            else:
                payload = to_send[:utils.MAX_PACKET_SIZE]
                packet = Packet(packet.src, packet.dest, True, False, payload)
                self.send(packet, dest)
                to_send = to_send[utils.MAX_PACKET_SIZE:]
