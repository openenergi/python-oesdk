import logging
import requests


class AuthApi():
    def __init__(
            self,
            username,
            password,
            base_url="https://api.openenergi.net/v1/"):
        logging.basicConfig()
        self.username = username
        self.password = password
        self.baseUrl = base_url

    def getJWT(self):
        token_resp = requests.post("{}auth".format(self.baseUrl),
                                   json={
            "username": self.username,
            "password": self.password
        })
        if token_resp.status_code != requests.codes.OK:
            logging.warning(
                "The HTTP response about the JWT is: '{}'".format(
                    token_resp.content))
            response.raise_for_status()
            raise ValueError(
                "The HTTP response code was not {}".format(
                    requests.codes.OK))
        token = token_resp.json()['token']
        return token

    def refreshJWT(self):
        '''
        TODO schedule this so it refreshes automatically when expiring
        '''
        self.JWT = self.getJWT()
        self.HttpHeaders = {"Authorization": "Bearer %s" % self.JWT,
                            "Content-Type": "application/json"}
