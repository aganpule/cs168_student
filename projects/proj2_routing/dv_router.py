"""Your awesome Distance Vector router for CS 168."""

import sim.api as api
import sim.basics as basics
import collections
import time
import copy
import pprint

# We define infinity as a distance of 16.
INFINITY = 16

class RoutingTable(object):
    def __init__(self, router):
        self.router = router
        # Maps port => latency
        self.neighbors = {}
        # Maps dst => {port: [latency, timestamp]}, where dst is a host address
        self.table = {}

    def add_host(self, port, dst):
        # self.update(port, address, self.neighbors[port])
        self.update(port, dst, 0)

    def add_neighbor(self, port, latency):
        # api.userlog.debug("Adding port %d as a neighbor to %s", port, api.get_name(self.router))
        self.neighbors[port] = latency

    def remove_neighbor(self, port):
        # api.userlog.debug("Removing port %d as a neighbor of %s", port, api.get_name(self.router))

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

        # curr_latency = self.table[dst][port][0] if (port in self.table[dst]) else INFINITY
        # if curr_latency < latency and (api.current_time() - self.table[dst][port][1] >)
        self.table[dst][port] = [latency, api.current_time()]

    def get_next_hop(self, dst):
        min_latency, next_hop = INFINITY, None
        expired = set()
        for port in self.table[dst]:
            latency, timestamp = self.table[dst][port]
            # Entry has expired, so remove it
            if latency != 0 and api.current_time() - timestamp > DVRouter.ROUTE_TIMEOUT:
                expired.add(port)
                continue
            total_latency = latency + self.neighbors[port]
            if total_latency < min_latency:
                min_latency = total_latency
                next_hop = port
        # for port in expired:
        #     del self.table[dst][port]
        return min_latency, next_hop

    def send_vector(self):
        for dst in self.table:
            min_latency, next_hop = self.get_next_hop(dst)
            # Unable to find route to dst
            if next_hop is None:
                if DVRouter.POISON_MODE: # TODO(not sure if this is right)
                    self.send_route_packet(dst, INFINITY, None)
                else:
                    continue
            else:
                self.send_route_packet(dst, min_latency, next_hop)

    def send_route_packet(self, dst, latency, next_hop):
        # TODO(should not be sending to host neighbors)
        for port in self.neighbors:
            # api.userlog.debug("%s is sending an update to port %d", api.get_name(self.router), port)
            if port == next_hop:
                if DVRouter.POISON_MODE:
                    self.router.send(basics.RoutePacket(dst, INFINITY))
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
            api.userlog.debug("Trying to send packet from %s to %s", api.get_name(packet.src), api.get_name(packet.dst))
            print api.get_name(self)
            print (self.table.neighbors)
            print (self.table.table)
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
        # First need to update our vector (in case things expired)
        # Go through each entry in routing table (by destination)
        # Remove entry if expired (if current time - entry time > 15s)
        # Take minimum total latency (total latency = time to neighbor + neighbor's distance to dst)
        # Then send our vector to all neighbors
        self.table.send_vector()
