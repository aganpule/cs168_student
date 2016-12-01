"""
Tests to see if routers will send packets along the shortest path, even if
they're directly connected to the destination host.
"""

import sim
import sim.api as api
import sim.basics as basics
import sys

from tests.test_simple import GetPacketHost, NoPacketHost

def launch():
    h1 = NoPacketHost.create('h1')
    h2 = GetPacketHost.create('h2')
    s1 = sim.config.default_switch_type.create('s1')
    s2 = sim.config.default_switch_type.create('s2')
    h1.linkTo(s1)
    s1.linkTo(h2, 3)
    s1.linkTo(s2)
    s2.linkTo(h2)

    def test_tasklet():
        yield 10

        api.userlog.debug('Sending ping from h1 to h2 - it should get through')
        h1.ping(h2)

        yield 5

        if c1.pings != 1:
            api.userlog.error("The first ping didn't get through")
            sys.exit(1)

        api.userlog.debug('Silently disconnecting s1 and s2')
        c1.enabled = False

        api.userlog.debug('Waiting for routes to time out')
        yield 20

        api.userlog.debug(
            'Sending ping from h1 to h2 - it should be dropped at s1')
        h1.ping(h2)

        yield 5

        if c1.pings != 1:
            api.userlog.error(
                's1 forwarded the ping when it should have dropped it')
            sys.exit(1)
        else:
            api.userlog.debug('s1 dropped the ping as expected')
            sys.exit(0)

    api.run_tasklet(test_tasklet)
