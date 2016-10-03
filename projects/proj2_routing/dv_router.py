"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics
import collections
import time

# We define infinity as a distance of 16.
INFINITY = 16

# Need to keep mapping of neighbor to latency
# Use this info to recalculate our vector
class RoutingTable(object):
    def __init__(self):
        # Maps port => [latency, destination]
        self.neighbors = {}
        # Maps dst => [latency, next_hop]
        self.vector = {}
        # Maps dst => {port: [latency, timestamp]}
        self.table = collections.defaultdict(dict)

    def add_host(self, port, address):
        self.neighbors[port][1] = address

    def add_neighbor(self, port, latency):
        self.neighbors[port] = [latency, None]

    def remove_neighbor(self, port):
        del self.neighbors[port]

    def update(self, port, dst, latency):
        self.table[dst][port] = [latency, time.clock()]

    def have_neighbor(self, address):
        # If I'm neighbors with this address, return the port associated with it.
        # Otherwise, return None
        for port in self.neighbors:
            if self.neighbors[port][1] == address:
                return port
        return None

    def recalculate_vector(self):
        for dst in self.vector:
            port = have_neighbor(dst)
            if port:
                # Do host discovery packets expire too?
                next_hop = port
                min_latency = self.neighbors[next_hop]
            else:
                min_latency = float('inf')
                next_hop = None
            for port in self.table[dst]:
                timestamp = self.table[dst][port][1]
                # Entry is expired
                if time.clock() - timestamp > 15:
                    # Remove the expired entry
                    del self.table[dst][port]
                    continue
                total_latency = self.table[dst][port][0] + self.neighbors[port]
                if total_latency < min_latency:
                    min_latency = total_latency
                    next_hop = port
            if next_hop is None:
                if POISON_MODE:
                    # Handle poison here
                    # Maybe we don't need this?
                else:
                    # If split horizon and no path, just remove from our vector
                    del self.vector[dst]
            self.vector[dst] = [min_latency, next_hop]

    def get_next_hop(dst):
        return self.vector[dst][1]

    def send_vector(self):
        # For every neighbor that's not a host
        for port in self.neighbors:
            is_host = self.neighbors[port][1] is not None
            if not is_host:
                for dst in self.vector:
                    if self.vector[dst][1] == port:
                        if POISON_MODE:
                            self.send(basics.RoutePacket(dst, INFINITY), port=port)
                        else:
                            # Split horizon, do nothing
                            continue
                    else:
                        self.send(basics.RoutePacket(dst, self.vector[dst][0]), port=port)


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
        self.table = RoutingTable()

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Learn about new link, add to routing table
        self.table.add_neighbor(port, latency)

    def handle_link_down(self, port):
        """
        Called by the framework when a link attached to this Entity does down.

        The port number used by the link is passed in.

        """
        self.table.remove_neighbor(port)

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
            self.table.update(port, packet.destination, packet.latency)
        # Discovering a new host that's a neighbor
        elif isinstance(packet, basics.HostDiscoveryPacket):
            # Add this host (packet.src) as a potential destination in our vector table
            # Latency would have already been determined in link up
            self.table.add_host(port, packet.src)
        # Just a regular data packet
        else:
            # Send the data packet to the port specified in our vector
            # First recalculate our vector
            # Then check if destination is in our vector
            # If not, drop the packet
            # Else, send to the next hop specified in our vector
            self.table.recalculate_vector()
            next_hop = self.table.get_next_hop(dst)
            if next_hop:
                self.send(packet, port=next_hop)
            # No way of getting there, so drop packet (do nothing)

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
        self.table.recalculate_vector()
        self.table.send_vector()
