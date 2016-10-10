"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics
import collections
import time
import copy
import pprint

# We define infinity as a distance of 16.
INFINITY = 16

class TableEntry(object):

    def __init__(self, latency):
        self.latency = latency
        self.timestamp = api.current_time()
        self.is_host = False

class NeighborsEntry(object):

    def __init__(self, latency):
        self.latency = latency
        self.is_host = False

class RoutingTable(object):
    def __init__(self, router):
        self.router = router
        # Maps port => NeighborsEntry
        self.neighbors = {}
        # Maps dst => TableEntry
        self.table = {}

    def add_host(self, port, dst):
        self.update(port, dst, 0)
        self.table[dst][port].is_host = True
        self.neighbors[port].is_host = True

    def add_neighbor(self, port, latency):
        self.neighbors[port] = NeighborsEntry(latency)

    def remove_neighbor(self, port):
        del self.neighbors[port]
        to_remove = set()
        for dst in self.table:
            for p in self.table[dst]:
                if p == port:
                    to_remove.add(dst)
        for elem in to_remove:
            del self.table[elem][port]


    def update(self, port, dst, latency):
        if dst not in self.table:
            self.table[dst] = {}
        self.table[dst][port] = TableEntry(latency)

    def get_next_hop(self, dst):
        min_latency, next_hop = INFINITY, None
        if dst not in self.table:
            return min_latency, next_hop
        expired = set()
        for port in self.table[dst]:
            entry = self.table[dst][port]
            # Entry has expired, so remove it
            if not entry.is_host and (api.current_time() - entry.timestamp) > DVRouter.ROUTE_TIMEOUT:
                expired.add(port)
                continue
            total_latency = entry.latency + self.neighbors[port].latency
            if total_latency < min_latency:
                min_latency = total_latency
                next_hop = port
        for port in expired:
            del self.table[dst][port]
        return min_latency, next_hop

    def send_vector(self, recipient_port=None):
        for dst in self.table:
            min_latency, next_hop = self.get_next_hop(dst)
            # Unable to find route to dst
            if next_hop is None:
                if DVRouter.POISON_MODE:
                    self.send_route_packet(dst, INFINITY, None, recipient_port)
                else:
                    continue
            else:
                self.send_route_packet(dst, min_latency, next_hop, recipient_port)

    def send_route_packet(self, dst, latency, next_hop, recipient_port):
        for port in self.neighbors:
            if (recipient_port and port != recipient_port) or self.neighbors[port].is_host:
                continue
            if port == next_hop:
                if DVRouter.POISON_MODE:
                    self.router.send(basics.RoutePacket(dst, INFINITY), port)
                else: # Split horizon; do nothing
                    continue
            else:
                self.router.send(basics.RoutePacket(dst, latency), port)

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
        self.table = RoutingTable(self)

    def handle_link_up(self, port, latency):
        """
        Called by the framework when a link attached to this Entity goes up.

        The port attached to the link and the link latency are passed
        in.

        """
        # Learn about new link, add to routing table
        self.table.add_neighbor(port, latency)
        # Eagerly initialize new neighbors
        self.table.send_vector(port)

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
            # Identify the next_hop port for this dst
            # If next_hop exists, send the packet to this port
            # Else, drop the packet
            dst = packet.dst
            min_latency, next_hop = self.table.get_next_hop(dst)

            if next_hop != None and next_hop != port:
                self.send(packet, port=next_hop)
            # No way of getting there, so drop packet (do nothing)

    def handle_timer(self):
        """
        Called periodically.

        When called, your router should send tables to neighbors.  It
        also might not be a bad place to check for whether any entries
        have expired.

        """
        # Send our vector to all neighbors
        self.table.send_vector()
