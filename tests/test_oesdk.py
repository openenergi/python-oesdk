import unittest
import oesdk
import os
import datetime
from pandas import Timestamp


class TestOesdk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.username = os.environ["OE_USERNAME"]
        cls.password = os.environ["OE_PASSWORD"]
        cls.entity_code = "l4662"

    def test_entity_api(cls):
        entity_api = oesdk.entity.EntityApi(cls.username, cls.password)
        entity_dict = entity_api.entityDetailsAsDict(cls.entity_code)
        assert entity_dict["code"] == "l4662"

        entity_hierarchy_dict = entity_api.explainHierarchy(cls.entity_code)
        assert entity_hierarchy_dict["EntityName"] == "SDK dummy load"

    def test_demand_api(cls):
        demand_api = oesdk.demand_profiles.DemandApi(cls.username, cls.password)
        target_date = datetime.datetime(2019, 12, 1).strftime("%Y-%m-%d")
        active_profile_df = demand_api.getActiveProfile(cls.entity_code, target_date)
        assert len(active_profile_df) >= 0 and len(active_profile_df) <= 48

        iso_weekday_id = datetime.datetime(2019, 12, 1).isoweekday()
        default_profile_df = demand_api.getDefaultProfile(
            cls.entity_code, iso_weekday_id
        )
        assert len(default_profile_df) >= 0 and len(default_profile_df) <= 48

    def test_historical_api(cls):
        historical_api = oesdk.historical_timeseries.HistoricalApi(
            cls.username, cls.password
        )
        power_variable = "active-power"

        raw_readings_df = historical_api.getRawReadings(
            "2019-12-01 10:00:00",
            Timestamp("2019-12-01 12:00:00"),
            variable=power_variable,
            entity_code=cls.entity_code,
        )
        assert len(raw_readings_df) == 3

        resampled_readings_df = historical_api.getResampledReadings(
            "2019-12-01 15",
            "2019-12-01 16:01",
            variable=power_variable,
            entity_code=cls.entity_code,
        )
        assert len(resampled_readings_df) == 3
