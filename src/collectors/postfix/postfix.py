# coding=utf-8

"""
Collect stats from postfix-stats. postfix-stats is a simple threaded stats
aggregator for Postfix. When running as a syslog destination, it can be used to
get realtime cumulative stats.

#### Dependencies

 * json
 * socket
 * StringIO
 * [postfix-stats](https://github.com/disqus/postfix-stats)

"""

import diamond.collector
import socket
from StringIO import StringIO

try:
    import json
except ImportError:
    import simplejson as json
    
class PostfixCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(PostfixCollector, self).get_default_config_help()
        config_help.update({
            'host': 'Hostname to coonect to',
            'port': 'Port to connect to',
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(PostfixCollector, self).get_default_config()
        config.update({
            'path':     'postfix',
            'host':     'localhost',
            'port':     7777,
        })
        return config
    
    def getJson(self):
        try:
            sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            sock.connect( (self.config['host'], int(self.config['port'])) )
            sock.send("stats\n")
            jsondata = sock.recv(4096)
            sock.close()
            return jsondata
        except socket.error:
            return None
    
    def getData(self):
        jsondata = self.getJson()
        io = StringIO(jsondata)
        data = json.load(io)
        return data

    def collect(self):
        data = self.getData()
        
        if not data:
            return
        
        for nodetype in data.keys():
            for nodesubtype in data[nodetype].keys():
                for metric in data[nodetype][nodesubtype].keys():
                    
                    # End metrics are sometimes codes like 2.0.0
                    metricname = metric.replace('.', '_')
                    
                    metric_name = "%s.%s.%s" % (nodetype, nodesubtype, metricname)
                    metric_value = data[nodetype][nodesubtype][metric]
                    
                    metric_value = self.derivative(metric_name, metric_value)
        
                    self.publish(metric_name, metric_value)
