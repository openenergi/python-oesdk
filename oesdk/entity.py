import logging

import requests

import oesdk.auth


class EntityApi():
    def __init__(
            self,
            username,
            password,
            base_url='https://api.openenergi.net/v1/'):
        self.auth = oesdk.auth.AuthApi(username, password, base_url)
        self.auth.refreshJWT()
        self.baseUrl = base_url

    def entityDetailsAsDict(self, entityCode):
        entity_response = requests.get(
            "{}entities/{}?expand_tags=true".format(self.baseUrl, entityCode),
            headers=self.auth.HttpHeaders
        )
        entity_details_dict = entity_response.json()
        return entity_details_dict

    # TODO provide option to return a Pandas dataframe instead of a dictionary
    def explainHierarchy(self, entityCode):
        """
        Given an input entityCode (for a device)
        it returns a dictionary with the ancestry (parent and gran-parent)
        along with the IP address
        """
        entity = self.entityDetailsAsDict(entityCode)
        parentEntity = self.entityDetailsAsDict(
            entity['asset_parent']) if 'asset_parent' in entity.keys() else {}
        grandParentEntity = self.entityDetailsAsDict(
            parentEntity['asset_parent']) if 'asset_parent' in parentEntity.keys() else {}
        ipAddress = ''
        if 'tags' in entity.keys():
            ipAddressList = [tag['value']
                             for tag in entity['tags'] if tag['key'] == 'ip']
            if len(ipAddressList) > 0:
                ipAddress = ipAddressList[0]
        info_dict = {
            'EntityName': entity['name'] if 'name' in entity.keys() else "",
            'EntityIpAddress': ipAddress,
            'ParentEntityCode': entity['asset_parent'] if 'asset_parent' in entity.keys() else "",
            'ParentName': parentEntity['name'] if 'name' in parentEntity.keys() else "",
            'GrandParentEntityCode': parentEntity['asset_parent'] if 'asset_parent' in parentEntity.keys() else "",
            'GrandParentName': grandParentEntity['name'] if 'name' in grandParentEntity.keys() else "",
        }
        return info_dict
