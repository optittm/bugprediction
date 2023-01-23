import glpi_api

class GlpiConnector:
    def __init__(self, url, appToken, userToken) -> None:
        self.url = url
        self.appToken = appToken
        self.userToken = userToken

        try:
            with glpi_api.connect(self.url, self.appToken, self.userToken) as glpi:
                print(glpi.get_config())
        except glpi_api.GLPIError as err:
            print(str(err))