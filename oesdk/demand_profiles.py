import datetime
import json
import logging

import pandas as pd
import requests

import oesdk.auth
import oesdk.time_helper


class DemandApi():
    def __init__(
            self,
            username,
            password,
            base_url='https://api.openenergi.net/v1/'):
        self.auth = oesdk.auth.AuthApi(username, password, base_url)
        self.auth.refreshJWT()
        self.baseUrl = base_url

    def upsertEmMode(self, entityCode):
        """
        Make sure the ingestion user is allowed to submit active profiles
        """
        em_mode_response = requests.patch(
            "{}demand-profiles/{}/mode".format(self.baseUrl, entityCode),
            headers=self.auth.HttpHeaders,
            json={"key": 'em-mode', "value": 'cd-mode'}
        )
        return em_mode_response

    def __upsertProfile(self, entityCode, httpBody, profileType):
        """
        Upsert any profile specified as a pandas DataFrame
        """
        em_mode_http_response = self.upsertEmMode(entityCode)
        if em_mode_http_response.status_code != requests.codes.NO_CONTENT:
            logging.warning(
                "The HTTP response about the Energy Manager mode is: '{}'".format(
                    em_mode_http_response.content))
            em_mode_http_response.raise_for_status()
            raise ValueError(
                "The HTTP response code was not {}".format(
                    requests.codes.NO_CONTENT))

        profile_response = requests.patch(
            "{}demand-profiles/{}/{}".format(self.baseUrl, entityCode, profileType),
            headers=self.auth.HttpHeaders,
            json=httpBody
        )
        if profile_response.status_code != 200:
            raise ValueError(
                "The Profile Upsert did not go as expected. "
                "The HTTP response code is '{}' "
                "and the HTTP response body is '{}' "
                "the HTTP request body was '{}'".format(
                    profile_response.status_code,
                    profile_response.text,
                    httpBody))
        upserted_profile_id = int(profile_response.text)
        return upserted_profile_id

    def upsertActiveProfile(
            self,
            entityCode,
            inDf,
            targetDateStr,
            metric_label='cd-power-target'):
        httpBody = map_metric_df_to_dict(inDf, metric_label)
        # inDf.iloc[0]['Timestamp'].strftime("%Y-%m-%d")
        httpBody["target_date"] = targetDateStr
        return self.__upsertProfile(entityCode, httpBody, "active")

    def upsertDefaultProfile(
            self,
            entityCode,
            inDf,
            weekDayId,
            metric_label='cd-power-target'):
        httpBody = map_metric_df_to_dict(inDf, metric_label)
        httpBody["week_day_id"] = int(weekDayId)
        return self.__upsertProfile(entityCode, httpBody, "default")

    def upsertActiveProfiles(
            self,
            entityCode,
            inDf,
            metric_label='cd-power-target'):
        inDf['Date'] = inDf["Timestamp"].map(lambda t: t.date())
        uniqueDates = inDf['Date'].unique()
        allDfsList = [inDf[(inDf['Date'] == x)] for x in uniqueDates]
        profileIdsList = [
            self.upsertActiveProfile(
                entityCode,
                currDf,
                currDf.iloc[0]['Date'].strftime("%Y-%m-%d"),
                metric_label) for currDf in allDfsList]
        return profileIdsList

    def getActiveProfile(self, load_code, target_date='2019-10-01'):
        if str(target_date).__contains__('/'):
            logging.warning(
                'target_date argument must have format YYYY-MM-DD: substituting / for - in string')
            target_date = target_date.replace('/', '-')
        return self.__getProfile(load_code, target_date, 'active')

    def getDefaultProfile(self, load_code, iso_week_day_id):
        valid_target_date = _getValidDateForWeekDayIdAsString(iso_week_day_id)
        # print("valid_target_date:", valid_target_date)
        default_profile_df = self.__getProfile(
            load_code, valid_target_date, 'default')
        return default_profile_df

    def __getProfile(
            self,
            load_code,
            target_date='2019-10-01',
            profileType='active'):
        if profileType == "active":
            meta_columns = [
                'profile_id', 'entity_code', 'target_date', [
                    'metrics', 'metric_name']]
        elif profileType == "default":
            meta_columns = [
                'default_profile_id', 'profile_id', 'entity_code', 'week_day_id', [
                    'metrics', 'metric_name']]
        else:
            raise ValueError(
                "Can not recognise this profile type: '{}'".format(profileType))
        # retrieve the profile
        res = requests.get(
            "{}demand-profiles/{}/{}?start={}".format(
                self.baseUrl,
                load_code,
                profileType,
                target_date
            ),
            headers=self.auth.HttpHeaders
        )
        # parse the JSON string
        dict_data = json.loads(res.text)
        if res.status_code != requests.codes.OK:
            logging.warning(
                'Error in profile API retrieval: No %s profile found for date %s for load %s' %
                (profileType, target_date, load_code))
            logging.warning(dict_data['message'])
            return None
        # de-normalise the JSON (nested lists) into a redundant dataframe
        df_profiles = pd.io.json.json_normalize(
            data=dict_data,
            record_path=['metrics', 'shape'],
            meta=meta_columns,
        )

        # pivot the metric column into multiple metric-lables columns
        # df_pivot = df_profiles.pivot(
        #                 columns='metrics.metric_name',
        #                  values='value'
        #              )

        # cannot pivot as get a whole bunch of NaNs; instead group by and
        # unstack to return a DF len(48):
        cols_to_gp = list(df_profiles.drop('value', axis=1).columns)
        if profileType != 'active':  # default, no target date so remove from grouping as well
            cols_to_gp = list(df_profiles.drop(['value'], axis=1).columns)

        df_pivot = df_profiles.set_index(cols_to_gp).unstack()[
            'value'].reset_index()
        df_pivot.rename_axis(columns=None, inplace=True)
        df_pivot.rename(
            columns={
                'halfhour_start': 'HalfhourStart'},
            inplace=True)

        if profileType == 'active':
            df_pivot['Date'] = pd.to_datetime(df_pivot['target_date']).dt.date
            df_pivot['Timestamp'] = df_pivot[['Date', 'HalfhourStart']].apply(
                lambda x: pd.Timestamp(x[0]) + datetime.timedelta(minutes=30 * (x[1] - 1)), axis=1)
            df_pivot['SettlementPeriod'] = df_pivot['Timestamp'].apply(
                lambda x: oesdk.time_helper.utc_to_settlement_period(x)[0])

        return df_pivot


def _getValidDateForWeekDayIdAsString(desiredIsoWeekDayId):
    '''
    ISO week day ID: 1-7
    '''
    today_utc = datetime.datetime.utcnow().replace(
        hour=0, minute=0, second=0, microsecond=0)
    today_isoweekday = today_utc.isoweekday()
    if today_isoweekday > desiredIsoWeekDayId:
        valid_day = today_utc + \
            datetime.timedelta(days=-(today_isoweekday - desiredIsoWeekDayId))
        return valid_day.strftime('%Y-%m-%d')
    if today_isoweekday < desiredIsoWeekDayId:
        valid_day = today_utc + \
            datetime.timedelta(days=-(7 + today_isoweekday - desiredIsoWeekDayId))
        return valid_day.strftime('%Y-%m-%d')
    return today_utc.strftime('%Y-%m-%d')


def map_metric_df_to_dict(in_shape_df, metric_lable):
    '''
    This is to be used with the Demand API (active/default profiles)
    '''
    # clone the dataframe before modifying it
    shape_df = in_shape_df.copy()
    shape_df.rename(
        columns={
            'HalfhourStart': 'halfhour_start',
            metric_lable: 'value'},
        inplace=True)
    p_dict = dict()
    power_metric = dict()
    power_metric["metric_name"] = metric_lable
    # we need to make sure each "halfhour_start" is of type int...
    # otherwise the JSON will contain a float instead...
    shape = list(map((lambda record: {"value": record["value"], "halfhour_start": int(
        record["halfhour_start"])}), shape_df[['halfhour_start', 'value']].to_dict(orient='records')))
    power_metric["shape"] = shape
    p_dict["metrics"] = [power_metric]
    return p_dict
