"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics
from collections import defaultdict

# We define infinity as a distance of 16.
INFINITY = 16

class DVRouter(basics.DVRouterBase):
    NO_LOG = True # Set to True on an instance to disable its logging
    POISON_MODE = False # Can override POISON_MODE here
    DEFAULT_TIMER_INTERVAL = 5 # Can override this yourself for testing

    def __init__(self):
        """
        Called when the instance is initialized.

        You probably want to do some additional initialization here.

        """
        self.start_timer()  # Starts calling handle_timer() at correct rate
        # maps dst => (latency, next_hop)
        self.vector = {}
        self.table = defaultdict(dict)

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Learn about new link, add to routing table and send your update
        if port not in self.vector:
            self.vector[port] = latency
        elif port in self.vector and self.vector[port] >= latency:
            self.vector[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        if not POISON_MODE:
            del self.vector[port]
        else:
            # handle poison
            pass

    # TODO
    def send_update(self, dst):
        pass
        # handle poisoning here

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        #self.log("RX %s on %s (%s)", packet, port, api.current_time())
        if isinstance(packet, basics.RoutePacket):
            dst = packet.destination
            self.table[port][dst] = packet.latency
            total_latency = packet.latency + self.vector[port][0]
            if dst in self.vector:
                if total_latency < self.vector[dst][0]:
                    self.vector[dst] = (total_latency, port)
                    self.send_update(dst)
            else:
                self.vector[dst] = (total_latency, port)
                self.send_update(dst)

        elif isinstance(packet, basics.HostDiscoveryPacket):
            pass
        else:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            try:
                next_hop = self.vector[packet.dst][1]
                self.send(packet, port=next_hop)
            except:
                pass # drop the packet
            # self.send(packet, port=port)

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        for neighbor in self.table:
            for dst in self.vector:
                packet = basics.RoutePacket(dst, self.vector[dst][0])
                self.send(packet, port=neighbor)
