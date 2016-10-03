"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics
import collections
import time

# We define infinity as a distance of 16.
INFINITY = 16

class DistanceVector:

    def __init__(self):
        self.vector = {}

    def add_dst(self, dst, latency, next_hop):
        self.vector[dst] = (latency, next_hop)

    def get_latency(dst):
        return self.vector[dst][0]

    def get_next_hop(dst):
        return self.vector[dst][1]



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
        self.table = collections.defaultdict(dict)

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Learn about new link, add to routing table and send your update
        # If this port is a new destination, send updates to all neighbors
        # If already in table, only send updates if vector is updated
        if port not in self.vector:
            self.vector[port] = latency
        elif port in self.vector and self.vector[port] >= latency:
            self.vector[port] = latency

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        # If poison mode, set distance
        # Send update to all neighbors
        if not POISON_MODE:
            del self.vector[port]
        else:
            # handle poison
            pass

    def handle_rx(self, packet, port):
        """
        Called by the framework when this Entity receives a packet.

        packet is a Packet (or subclass).
        port is the port number it arrived on.

        You definitely want to fill this in.

        """
        # self.log("RX %s on %s (%s)", packet, port, api.current_time())
        # Getting an update from a neighbor
        if isinstance(packet, basics.RoutePacket):
            # Update our routing table with new info, including the time received
            pass
        # Discovering a new host that's a neighbor
        elif isinstance(packet, basics.HostDiscoveryPacket):
            # Add this host (packet.src) as a potential destination in our vector table
            # Latency???
            pass
        # Just a regular data packet
        else:
            # Send the data packet to the port specified in our vector
            # First recalculate our vector
            # Then check if destination is in our vector
            # If not, drop the packet
            # Else, send to the next hop specified in our vector

            # THIS IS NOT OUR CODE:
            # Totally wrong behavior for the sake of demonstration only: send
            # the packet back to where it came from!
            # self.send(packet, port=port) # THIS IS WRONG
            pass

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        # First need to update our vector (in case things expired)
        # Go through each entry in routing table (by destination)
        # Remove entry if expired (if current time - entry time > 15s)
        # Take minimum total latency (total latency = time to neighbor + neighbor's distance to dst)
        # Then send our vector to all neighbors
        pass
        # total_latency = packet.latency + self.vector[port][0]
        # if dst in self.vector:
        #     if total_latency < self.vector[dst][0]:
        #         self.vector[dst] = (total_latency, port)
        #         self.send_update(dst)
        # else:
        #     self.vector[dst] = (total_latency, port)
        #     self.send_update(dst)
