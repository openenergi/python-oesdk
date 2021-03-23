import concurrent.futures
import logging
import random
import time

import pandas as pd
import requests

import oesdk.auth
import oesdk.time_helper

MAX_LIMIT = 200000


def map_variable_to_resampling_method(variable):
    if variable == 'n2ex-forecast':
        resampling = '1h'
    elif variable == 'baseline-forecast':
        resampling = '30m'
    else:  # active-power, avail, resp etc
        resampling = '30m-compliance'
    return resampling


class HistoricalApi():
    def __init__(
            self,
            username,
            password,
            base_url='https://api.openenergi.net/v1/'):
        self.auth = oesdk.auth.AuthApi(username, password, base_url)
        self.auth.refreshJWT()
        self.baseUrl = base_url

    def getResampledReadings(
            self,
            start,
            end,
            variable,
            entity_code):
        # validate dates...
        start = oesdk.time_helper.to_iso_ts_zulu(start)
        end = oesdk.time_helper.to_iso_ts_zulu(end)
        # find out the resampling method
        resampling = map_variable_to_resampling_method(variable)
        # build the URL for the API request
        api_http_route = "{}timeseries/historical/readings/points/{}/resamplings/{}?entity={}&start={}&finish={}&limit={}".format(
            self.baseUrl, variable, resampling, entity_code, start, end, MAX_LIMIT)
        logging.info(
            "Retrieving resampled readings for entity code {}, variable {}, start time {}, end time {}".format(
                entity_code,
                variable,
                start,
                end))
        # print(api_http_route)
        res = requests.get(
            api_http_route,
            headers=self.auth.HttpHeaders
        )
        if res.status_code != requests.codes.OK:
            logging.warning(
                "The HTTP response about the retrieval of resampled readings is: '{}'".format(
                    res.status_code))
            res.raise_for_status()
            raise ValueError(
                "The HTTP response code was not {}".format(
                    requests.codes.OK))
        # print(res.json())
        df = pd.DataFrame.from_dict(res.json()['items'])
        df.rename(columns={
            'time': 'Time',
            'key': 'EntityCode',
            'value': variable,
        }, inplace=True)
        df['Type'] = resampling  # resampling or "raw"
        # print()
        # print(df.head())
        return df

    def __getRawReadings(
            self,
            start,
            end,
            variable,
            entity_code,
            wait_before_request=0):
        """
        If no data is found, then it returns None.
        Otherwise it returns a dataframe.
        """
        # validate dates...
        if start[-1] != 'Z' or end[-1] != 'Z':
            raise ValueError("The time filters are not in Zulu format")
        api_http_route = "{}timeseries/historical/readings/points/{}/raw?entity={}&start={}&finish={}".format(
            self.baseUrl, variable, entity_code, start, end)
        logging.debug(
            "Retrieving raw readings for entity code {}, variable {}, start time {}, end time {} (wait_before_request? {} seconds)".format(
                entity_code,
                variable,
                start,
                end,
                wait_before_request))
        if wait_before_request > 0:
            time.sleep(wait_before_request)
        # print(api_http_route)
        res = requests.get(
            api_http_route,
            headers=self.auth.HttpHeaders
        )
        if res.status_code != requests.codes.OK:
            logging.warning(
                "The HTTP response about the retrieval of raw readings is: '{}'".format(
                    res.status_code))
            res.raise_for_status()
            raise ValueError(
                "The HTTP response code was not {}".format(
                    requests.codes.OK))
        # print(res.json())
        df = pd.DataFrame.from_dict(res.json()['items'])
        if len(df) == 0:
            logging.warning(
                "No data found for entity_code {}, variable {}, start {}, end {}".format(
                    entity_code, variable, start, end, ))
            return None
        df['time'] = pd.DatetimeIndex(df['time'])
        df.set_index(df['time'], inplace=True, verify_integrity=False)
        # TODO use an index to enforce the order on timestamps...
        df.rename(columns={
            'time': 'Time',
            'key': 'EntityCode',
            'value': variable,
        }, inplace=True)
        # print(df.head())
        df.drop(columns=['type'], inplace=True)
        df['Type'] = 'raw'
        logging.info(
            "Done retrieving raw readings for entity code {}, variable {}, start {}, end {}".format(
                entity_code,
                variable,
                start,
                end,
            ))
        return df

    def getRawReadings(
            self,
            start,
            end,
            variable,
            entity_code):
        _1h_time_chops = oesdk.time_helper.get_datetime_slices(
            start, end)
        df_list = []
        # 6 threads seems the optimal number for 1-hour slices concurrent HTTP
        # requests
        num_threads = min(6, len(_1h_time_chops))
        jobs = []
        with concurrent.futures.ThreadPoolExecutor(num_threads) as tpe:
            for _1h_slice in _1h_time_chops:
                curr_random_sleep = random.random() * 0.5
                jobs.append(
                    tpe.submit(
                        self.__getRawReadings,
                        _1h_slice[0], _1h_slice[1],
                        variable, entity_code,
                        curr_random_sleep
                    )
                )
            for job in concurrent.futures.as_completed(jobs):
                curr_df = job.result()
                if curr_df is not None:
                    df_list.append(curr_df)
        # sort on the DatetimeIndex
        full_df = pd.concat(df_list, sort=True)
        full_df.sort_index(inplace=True)
        logging.info(
            "Returning a dataframe with raw data with length: {}".format(
                len(full_df)))
        return full_df
