#!/usr/bin/python
# coding=utf-8
################################################################################

from test import CollectorTestCase
from test import get_collector_config
from test import unittest
from mock import Mock
from mock import call
from mock import patch

from diamond.collector import Collector
from megaraid import MegaRAIDCollector

################################################################################


class TestMegaRAIDCollector(CollectorTestCase):
    def setUp(self):
        config = get_collector_config('MegaRAIDCollector', {
            'interval': 600,
            'bin': 'true',
        })

        self.collector = MegaRAIDCollector(config, None)

    def test_import(self):
        self.assertTrue(MegaRAIDCollector)

    @patch.object(Collector, 'publish')
    def test_should_work_with_real_data(self, publish_mock):
        patch_communicate = patch(
            'subprocess.Popen.communicate',
            Mock(side_effect=[
                (self.getFixture('physical').getvalue(), ''),
                (self.getFixture('virtual').getvalue(), ''),
                (self.getFixture('bbu').getvalue(), '')]))
        patch_communicate.start()
        self.collector.collect()
        patch_communicate.stop()

        self.assertPublishedMany(publish_mock, {
            'pd.adapter0.phy0.media_errors': 60,
            'pd.adapter0.phy0.other_errors': 1,
            'pd.adapter0.phy0.predictive_failures': 0,
            'pd.adapter0.phy0.temperature': 32,
            'pd.adapter0.phy0.smart_alert': 0,
            'pd.adapter0.phy1.media_errors': 3,
            'pd.adapter0.phy1.other_errors': 0,
            'pd.adapter0.phy1.predictive_failures': 0,
            'pd.adapter0.phy1.temperature': 37,
            'pd.adapter0.phy1.smart_alert': 0,
            'pd.adapter0.phy2.media_errors': 21,
            'pd.adapter0.phy2.other_errors': 0,
            'pd.adapter0.phy2.predictive_failures': 0,
            'pd.adapter0.phy2.temperature': 36,
            'pd.adapter0.phy2.smart_alert': 0,
            'pd.adapter0.phy3.media_errors': 21,
            'pd.adapter0.phy3.other_errors': 0,
            'pd.adapter0.phy3.predictive_failures': 0,
            'pd.adapter0.phy3.temperature': 33,
            'pd.adapter0.phy3.smart_alert': 0,
            'pd.adapter0.phy4.media_errors': 5,
            'pd.adapter0.phy4.other_errors': 1,
            'pd.adapter0.phy4.predictive_failures': 0,
            'pd.adapter0.phy4.temperature': 37,
            'pd.adapter0.phy4.smart_alert': 0,
            'pd.adapter0.phy5.media_errors': 28,
            'pd.adapter0.phy5.other_errors': 0,
            'pd.adapter0.phy5.predictive_failures': 0,
            'pd.adapter0.phy5.temperature': 35,
            'pd.adapter0.phy5.smart_alert': 1,
            'vd.adapter0.virt0.raid_level': 1,
            'vd.adapter0.virt0.state_optimal': 1,
            'vd.adapter0.virt0.drives': 2,
            'vd.adapter0.virt0.cache_policy_default': 1,
            'vd.adapter0.virt0.bad_blocks': 0,
            'vd.adapter0.virt1.raid_level': 0,
            'vd.adapter0.virt1.state_optimal': 1,
            'vd.adapter0.virt1.drives': 1,
            'vd.adapter0.virt1.cache_policy_default': 1,
            'vd.adapter0.virt1.bad_blocks': 1,
            'vd.adapter0.virt2.raid_level': 0,
            'vd.adapter0.virt2.state_optimal': 1,
            'vd.adapter0.virt2.drives': 1,
            'vd.adapter0.virt2.cache_policy_default': 1,
            'vd.adapter0.virt2.bad_blocks': 0,
            'vd.adapter0.virt3.raid_level': 0,
            'vd.adapter0.virt3.state_optimal': 1,
            'vd.adapter0.virt3.drives': 1,
            'vd.adapter0.virt3.cache_policy_default': 1,
            'vd.adapter0.virt3.bad_blocks': 1,
            'vd.adapter0.virt4.raid_level': 0,
            'vd.adapter0.virt4.state_optimal': 1,
            'vd.adapter0.virt4.drives': 1,
            'vd.adapter0.virt4.cache_policy_default': 1,
            'vd.adapter0.virt4.bad_blocks': 0,
            'vd.adapter0.virt5.raid_level': 0,
            'vd.adapter0.virt5.state_optimal': 1,
            'vd.adapter0.virt5.drives': 1,
            'vd.adapter0.virt5.cache_policy_default': 0,
            'vd.adapter0.virt5.bad_blocks': 0,
            'bbu.adapter0.voltage': 4073,
            'bbu.adapter0.current': 0,
            'bbu.adapter0.temperature': 27,
            'bbu.adapter0.fw.voltage': 1,
            'bbu.adapter0.fw.temperature': 1,
            'bbu.adapter0.fw.learn_cycle_requested': 0,
            'bbu.adapter0.fw.learn_cycle_active': 0,
            'bbu.adapter0.fw.learn_cycle_status': 1,
            'bbu.adapter0.fw.learn_cycle_timeout': 0,
            'bbu.adapter0.fw.i2c_errors_detected': 0,
            'bbu.adapter0.fw.battery_pack_missing': 0,
            'bbu.adapter0.fw.battery_replacement_required': 0,
            'bbu.adapter0.fw.remaining_capacity_low': 0,
            'bbu.adapter0.fw.periodic_learn_required': 0,
            'bbu.adapter0.fw.transparent_learn': 0,
            'bbu.adapter0.fw.no_space_to_cache_offload': 0,
            'bbu.adapter0.fw.pack_is_about_to_fail': 0,
            'bbu.adapter0.fw.cache_offload_premium_feature_required': 0,
            'bbu.adapter0.fw.module_microcode_update_required': 0,
            'bbu.adapter0.gasgauge.fully_discharged': 0,
            'bbu.adapter0.gasgauge.fully_charged': 1,
            'bbu.adapter0.gasgauge.discharging': 1,
            'bbu.adapter0.gasgauge.initialized': 1,
            'bbu.adapter0.gasgauge.remaining_time_alarm': 0,
            'bbu.adapter0.gasgauge.discharge_terminated': 0,
            'bbu.adapter0.gasgauge.over_temperature': 0,
            'bbu.adapter0.gasgauge.charging_terminated': 1,
            'bbu.adapter0.gasgauge.over_charged': 0,
            'bbu.adapter0.relative_state_of_charge': 100,
            'bbu.adapter0.remaining_capacity': 1559,
            'bbu.adapter0.full_charge_capacity': 1559,
            'bbu.adapter0.issohgood': 1,
            'bbu.adapter0.gasgauge.battery_backup_charge_time': 0,
            'bbu.adapter0.capacity.relative_state_of_charge': 100,
            'bbu.adapter0.capacity.absolute_state_of_charge': 87,
            'bbu.adapter0.capacity.remaining_capacity': 1559,
            'bbu.adapter0.capacity.full_charge_capacity': 1559,
            'bbu.adapter0.capacity.cycle_count': 44,
            'bbu.adapter0.design.design_capacity': 1800,
            'bbu.adapter0.design.design_voltage': 3700,
        })


################################################################################
if __name__ == "__main__":
    unittest.main()
