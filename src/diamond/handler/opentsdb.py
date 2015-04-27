# coding=utf-8

"""
Send metrics to a [OpenTSDB](http://opentsdb.net/) 2 server.

[OpenTSDB](http://opentsdb.net/) is a distributed, scalable Time Series
Database (TSDB) written on top of [HBase](http://hbase.org/). OpenTSDB was
written to address a common need: store, index and serve metrics collected from
computer systems (network gear, operating systems, applications) at a large
scale, and make this data easily accessible and graphable.

This handler will only work with OpenTSDB servers version >=2 as it uses the
HTTP API introduced in OpenTSDB2. If you are using an earlier version, you
may try TSDBHandler.

#### Dependencies

 * [requests](http://docs.python-requests.org/)

#### Configuration

Enable this Handler
 
 * handlers = diamond.handler.opentsdb.OpenTSDBHandler,

 * servers = List of opentsdb servers
     Ex: "192.168.1.2:4242", "192.168.1.3:4242", "192.168.1.4:4242"
     Handler will select one at random and send data to that server.
     If communication fails for any reason, handler will try next
     server in the list until all servers have been tried. If all
     fails batch will be dropped.
     Default: "localhost:4242"
 * timeout = Connection and request timeout in seconds
     Default: 5
 * batchsize = Number of metrics to send in one request
     OpenTSDB HTTP API allows more than one datapoint to be sent in
     one request for greater throughput. Handler will accumulate
     this much metrics and send them in one request.
     Default = 10
 * tags = List of tags to be added to all metrics
     Ex: "dc=eu", "cluster=web"
     Can be used to aggregate machines with common properties
     Default = []
 * tagsinmetric = List of regexes to extract tags from metrics
     Ex: "cpu\.(?P<core>\w+)\..+", "diskspace\.(?P<mount>\w+)\..+"
     Some metrics for some collectors may be inefficient to store
     directly in OpenTSDB, as they will create too much distinct
     metrics. Using these regexes, handler is able to post-process
     diamond metricnames into more opentsdb-friendly metric-tag
     combinations. Above example will simply do:

     * cpu.cpu0.idle -> metric: cpu.idle tags: core=cpu0
     * cpu.cpu1.idle -> metric: cpu.idle tags: core=cpu1
     * diskspace.root.byte_free -> metric: diskspace.byte_free tags: mount=root

     Default = []


"""

from Handler import Handler
import requests
import json
import random
import re

class OpenTSDBHandler(Handler):
    """
    Implements the abstract Handler class, sending data to opentsdb 2
    """
    DOTS = re.compile("\.+")
    COLONS = re.compile(":+")

    def __init__(self, config=None):
        """
        Create a new instance of the OpenTSDBHandler class
        """
        # Initialize Handler
        Handler.__init__(self, config)

        # Initialize Options
        self.timeout = int(self.config['timeout'])
        self.batchsize = int(self.config['batchsize'])

        servers = self.config['servers']
        # Force servers to be a list
        if isinstance(servers, basestring):
            servers = [servers]

        tags = self.config['tags']
        # Force tags to be a list
        if isinstance(tags, basestring):
            tags = [tags]
        # Parse tags 
        tags = [tuple(t.split("=")) for t in tags if t.find("=") > 0]
        self.tags = dict(tags)

        tagsinmetric = self.config['tagsinmetric']
        # Force tagsinmetric to be a list
        if isinstance(tagsinmetric, basestring):
            tagsinmetric = [tagsinmetric]
        # Parse regexes
        self.tagsinmetric = [re.compile(t) for t in tagsinmetric]

        self.session = requests.Session()
        self.endpoints = ["http://%s/api/put" % h for h in servers]
        # Select one at random to be the main server
        self.mainep = random.randint(0, len(self.endpoints) - 1)
        self.batch = []

    def get_default_config_help(self):
        """
        Returns the help text for the configuration options for this handler
        """
        config = super(OpenTSDBHandler, self).get_default_config_help()

        config.update({
            'servers': 'OpenTSDB2 server(s)',
            'timeout': 'Connection and/or request timeout',
            'batchsize': 'Send this much metrics in one request',
            'tags': 'Tags to add to all metrics (in addition to the hostname)',
            'tagsinmetric': 'Tags to extract from metrics (regex)',
        })

        return config

    def get_default_config(self):
        """
        Return the default config for the handler
        """
        config = super(OpenTSDBHandler, self).get_default_config()

        config.update({
            'servers': ['localhost:4242'],
            'timeout': 5,
            'batchsize': 10,
            'tags': [],
            'tagsinmetric': [],
        })

        return config

    def __del__(self):
        """
        Destroy instance of the OpenTSDBHandler class
        """
        self._close()

    def process(self, metric):
        """
        Convert metric to OpenTSDB2 HTTP API format and send
        """

        tags = {"hostname": metric.host}
        tags.update(self.tags)
        mpp = metric.path.split('.')
        if mpp[0] == 'instances':
            tags.update({'instance': mpp[1]})
        metricname = u'.'.join(mpp[2:])
        for rgx in self.tagsinmetric:
            rgm = rgx.match(metricname)
            if rgm is not None:
                metrictags = rgm.groupdict()
                tags.update(metrictags)
                for tagval in metrictags.values():
                    metricname = metricname.replace(tagval, "")

        # TSDB does not allow : in metric names
        metricname = self.COLONS.sub("_", metricname)
        # Normalize any double dots
        metricname = self.DOTS.sub(".", metricname)
        data = {
            u"metric": metricname,
            u"timestamp": metric.timestamp,
            u"value": metric.value,
            u"tags": tags,
        }
        self.batch.append(data)
        if len(self.batch) >= self.batchsize:
            self._send(self.batch)
            self.batch = []

    def _send(self, data, to = -1):
        """
        Send data to OpenTSDB2 server. Will try next server if main fails.
        """
        if to < 0:
            to = self.mainep
        elif to == self.mainep:
            self.log.error("OpenTSDBHandler: Servers exhausted")
            return
        url = self.endpoints[to]
        try:
            res = self.session.post(
                url,
                data = json.dumps(data),
                timeout = self.timeout)
            if res.status_code >= 400:
                self.log.warning("OpenTSDBHandler: Server returns %d: %s" % (
                    res.status_code, res.content))
            # release the connection
            rc = res.close()
        except requests.ConnectionError, e:
            self.log.error("OpenTSDBHandler: Failed sending, trying next. %s", e)
            self._send(data, (to + 1) % len(self.endpoints))

    def _close(self):
        """
        Send remaining data and close the session
        """
        if len(self.batch) > 0:
            self._send(self.batch)
            self.batch = []
        if self.session is not None:
            self.session.close()
        self.session = None
