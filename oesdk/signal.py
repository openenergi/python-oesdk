import pandas as pd
import requests
import oesdk.auth


class SignalApi:
    def __init__(self, username, password, base_url="https://api.openenergi.net/v1/"):
        self.auth = oesdk.auth.AuthApi(username, password, base_url)
        self.auth.refreshJWT()
        self.baseUrl = base_url

    def dispatch_signal_to_entity(self, df, load_code, signal_type="variable-adjust"):
        message = build_signal_body(df, load_code, signal_type=signal_type)
        response = requests.post(
            self.baseUrl + "signals",
            headers=self.auth.HttpHeaders,
            json=message,
        )
        if response.status_code != requests.codes.accepted:
            response.raise_for_status()
        return response


def build_signal_body(df, load_code, signal_type="variable-adjust"):
    # make sure there is a datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        msg = "Dataframe should have a DateTime index"
        raise RuntimeError(msg)
    # extract the signal components
    content_list = []
    for time, row in df.iterrows():
        values = []
        for col in df.columns:
            values.append({"variable": col, "value": float(row[col])})
        content_list.append({"start_at": time.isoformat(), "values": values})
    # build the signal body (to be sent as JSON)
    signal_body = {
        "target": {"entity": load_code},
        "content": content_list,
        "type": signal_type,
    }
    return signal_body
