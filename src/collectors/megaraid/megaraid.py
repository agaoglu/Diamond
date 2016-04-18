# coding=utf-8

"""
Collect data from lsi MegaRAID command-line utility

#### Dependencies

 * [megacli](http://www.lsi.com/support/Pages/download-results.aspx?keyword=megacli)

"""

import diamond.collector
import subprocess
import re
import os
from diamond.collector import str_to_bool


class MegaRAIDCollector(diamond.collector.Collector):

    def get_default_config_help(self):
        config_help = super(MegaRAIDCollector, self).get_default_config_help()
        config_help.update({
            'bin':         'The path to the MegaCli binary',
            'use_sudo':    'Use sudo?',
            'sudo_cmd':    'Path to sudo',
        })
        return config_help

    def get_default_config(self):
        """
        Returns default configuration options.
        """
        config = super(MegaRAIDCollector, self).get_default_config()
        config.update({
            'path': 'megaraid',
            'bin': 'MegaCli64',
            'use_sudo':         False,
            'sudo_cmd':         '/usr/bin/sudo',
        })
        return config

    def collect(self):
        """
        Collect and publish MegaRAID values
        """
        self._collect_physical()
        self._collect_virtual()
        self._collect_bbu()

    def _collect_physical(self):
        command = [self.config['bin'], "-PDList", "-aALL", "-NoLog"]

        if str_to_bool(self.config['use_sudo']):
            command.insert(0, self.config['sudo_cmd'])

        output = subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        ).communicate()[0].strip().splitlines()

        metrics = {}

        adapter = 0
        slot = 0

        for line in output:
            line = line.strip()
            if line == "":
                continue
            if line.startswith("Adapter #"):
                adapter = int(line[9:])
                continue
            if line.startswith("Enclosure Device ID: "):
                continue
            if line.startswith("Slot Number: "):
                slot = int(line[13:])
                continue
            if line.startswith("Exit Code: "):
                continue
            linedata = line.split(":")
            if len(linedata) == 2:
                key = linedata[0].strip()
                value = linedata[1].strip()
                if key == "Media Error Count":
                    metrics["pd.adapter%d.phy%d.media_errors" % (adapter, slot)] = int(value)
                if key == "Other Error Count":
                    metrics["pd.adapter%d.phy%d.other_errors" % (adapter, slot)] = int(value)
                if key == "Predictive Failure Count":
                    metrics["pd.adapter%d.phy%d.predictive_failures" % (adapter, slot)] = int(value)
                if key == "Drive Temperature" and value != "N/A":
                    metrics["pd.adapter%d.phy%d.temperature" % (adapter, slot)] = int(value[:value.find('C')])
                if key == "Drive has flagged a S.M.A.R.T alert":
                    metrics["pd.adapter%d.phy%d.smart_alert" % (adapter, slot)] = int(str_to_bool(value))

        for name, metric in metrics.items():
            self.publish(name, metric)

    def _collect_virtual(self):
        command = [self.config['bin'], "-LDInfo", "-Lall", "-aALL", "-NoLog"]

        if str_to_bool(self.config['use_sudo']):
            command.insert(0, self.config['sudo_cmd'])

        output = subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        ).communicate()[0].strip().splitlines()

        metrics = {}

        adapter = 0
        vd = 0
        default_cache_policy = ""

        for line in output:
            line = line.strip()
            if line == "":
                continue
            if line.startswith("Adapter "):
                adapter = int(line[8:line.find(' ', 8)])
                continue
            if line.startswith("Virtual Drive: "):
                vd = int(line[15:line.find(' ', 15)])
                continue
            if line.startswith("Exit Code: "):
                continue
            linedata = line.split(":")
            if len(linedata) == 2:
                key = linedata[0].strip()
                value = linedata[1].strip()
                if key == "RAID Level":
                    metrics["vd.adapter%d.virt%d.raid_level" % (adapter, vd)] = int(value[8:9])
                if key == "State":
                    metrics["vd.adapter%d.virt%d.state_optimal" % (adapter, vd)] = int(value == "Optimal")
                if key == "Number Of Drives":
                    metrics["vd.adapter%d.virt%d.drives" % (adapter, vd)] = int(value)
                if key == "Default Cache Policy":
                    default_cache_policy = value
                if key == "Current Cache Policy":
                    metrics["vd.adapter%d.virt%d.cache_policy_default" % (adapter, vd)] = int(value == default_cache_policy)
                if key == "Bad Blocks Exist":
                    metrics["vd.adapter%d.virt%d.bad_blocks" % (adapter, vd)] = int(str_to_bool(value))

        for name, metric in metrics.items():
            self.publish(name, metric)

    def _collect_bbu(self):
        command = [self.config['bin'], "-AdpBbuCmd", "-aAll", "-NoLog"]

        if str_to_bool(self.config['use_sudo']):
            command.insert(0, self.config['sudo_cmd'])

        output = subprocess.Popen(
            command,
            stdout=subprocess.PIPE
        ).communicate()[0].strip().splitlines()

        metrics = {}

        adapter = 0
        section = ''

        for line in output:
            if line.strip() == "":
                continue
            if line.startswith("BBU status for Adapter: "):
                adapter = int(line[24:])
                continue
            if line.startswith("Exit Code: "):
                continue
            if line.startswith("BBU Firmware Status:"):
                section = "fw"
                continue
            if line.startswith("GasGuageStatus:"):
                section = "gasgauge"
                continue
            if line.startswith("BBU Capacity Info"):
                section = "capacity"
                continue
            if line.startswith("BBU Design Info"):
                section = "design"
                continue
            if line.startswith("BBU Properties"):
                section = "prop"
                continue
            linedata = line.split(":")
            if len(linedata) == 2:
                key = self.slugify(linedata[0].strip())
                value = self.nounit(linedata[1].strip())
                if linedata[0].startswith(" "):
                    key = "%s.%s" % (section, key)
                if value is not None:
                    metrics["bbu.adapter%d.%s" % (adapter, key)] = value

        for name, metric in metrics.items():
            self.publish(name, metric)

    def slugify(self, key):
        if key.find("&") > 0:
            key = key[:key.find('&')].strip()
        return key.lower().replace(" ", "_")

    def nounit(self, value):
        try:
            if value == "OK":
                return 1
            if unicode(value).isnumeric():
                return int(value)
        except UnicodeDecodeError:
            pass
        valwords = value.split(" ")
        if len(valwords) == 2 and unicode(valwords[0]).isnumeric():
            return int(valwords[0])
        try:
            return int(str_to_bool(value.lower()))
        except NotImplementedError:
            return None
