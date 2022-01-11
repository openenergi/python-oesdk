import unittest
import os
import datetime
from oesdk.demand_profiles import DemandApi
from oesdk.entity import EntityApi
from oesdk.historical_timeseries import HistoricalApi
from pandas import Timestamp


class TestOesdk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username = os.environ["OE_USERNAME"]
        cls.password = os.environ["OE_PASSWORD"]
        cls.entity_code = "L2510"

    def test_entity_api(self):
        entity_api = EntityApi(self.username, self.password)
        entity_dict = entity_api.entityDetailsAsDict(self.entity_code)
        assert entity_dict["code"].upper() == self.entity_code.upper()

        entity_hierarchy_dict = entity_api.explainHierarchy(self.entity_code)
        assert entity_hierarchy_dict["EntityName"] == "Battery"

    def test_demand_api(self):
        demand_api = DemandApi(self.username, self.password)
        target_date = datetime.datetime(2021, 12, 1).strftime("%Y-%m-%d")
        active_profile_df = demand_api.getActiveProfile(self.entity_code, target_date)
        assert len(active_profile_df) >= 0 and len(active_profile_df) <= 48

        iso_weekday_id = datetime.datetime(2021, 12, 1).isoweekday()
        default_profile_df = demand_api.getDefaultProfile(
            self.entity_code, iso_weekday_id
        )
        assert len(default_profile_df) >= 0 and len(default_profile_df) <= 48

    def test_historical_api(self):
        historical_api = HistoricalApi(self.username, self.password)
        power_variable = "active-power"

        raw_readings_df = historical_api.getRawReadings(
            "2021-12-01 10:00:00",
            Timestamp("2021-12-01 10:01:00"),
            variable=power_variable,
            entity_code=self.entity_code,
        )
        assert len(raw_readings_df) == 32

        resampled_readings_df = historical_api.getResampledReadings(
            "2019-12-01 15",
            "2019-12-01 16:01",
            variable=power_variable,
            entity_code=self.entity_code,
        )
        assert len(resampled_readings_df) == 3
