####################################################################
# FILENAME: stats/__init__.py
# PROJECT: Shiji API
# DESCRIPTION: Implements stats support for Shiji web API framework.
#
#
# $Id$
####################################################################
# (C)2015 DigiTar Inc.
# Licensed under the MIT License.
####################################################################
import os,sys
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')

sys.path.append(vendor_dir)

from txstatsd.client import (TwistedStatsDClient, StatsDClientProtocol)
from txstatsd.metrics.metrics import Metrics

class FakeStatsDClient(object):

    def connect(self):
        """Connect to the StatsD server."""
        pass

    def disconnect(self):
        """Disconnect from the StatsD server."""
        pass

    def write(self, data):
        """Send the metric to the StatsD server."""
        self.data = data

# Default metrics to using a fake provider.
metrics = Metrics(FakeStatsDClient(), 'webprotectme.null')

def install_stats(host, port, scheme):
    global metrics
    
    statsd_client = TwistedStatsDClient(host, port)
    metrics = Metrics(connection=statsd_client,
                      namespace=scheme)
    return StatsDClientProtocol(statsd_client)