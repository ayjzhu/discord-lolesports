import os
import requests
from dotenv import load_dotenv
from enum import Enum

load_dotenv()
# API_BASE = os.getenv('API_BASE')
# X_API_KEY = os.getenv('X_API_KEY')
class Region(Enum):
    LPL = 98767991314006698
    LCK = 98767991310872058
    LEC = 98767991302996019
    LCS = 98767991299243165
    PCS = 104366947889790212
    WORLDS = 98767975604431411

class LolEsports:
    # optional region parameter
    def __init__(self, region: Region = Region.LEC):
        self.api_base = os.getenv('API_BASE')
        self.x_api_key = os.getenv('X_API_KEY')
        self.region = region
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Referer': 'https://lolesports.com/',
            "x-api-key": self.x_api_key
        }

    def get_live(self):
        result = ''
        payload = {
            'hl': 'en-US'
        }

        url = f'{self.api_base}/getLive'
        response = requests.get(url, params=payload, headers=self.headers)
        print(response)

        live_events = response.json()['data']['schedule']['events']
        if len(live_events) == 0:
            result = "No live event!"
        else:
            for live_event in live_events:
                result += "event id: {}\n".format(live_event['id'])
                if live_event['type'] == 'show':
                    result += '{} pre-{} is starting'.format(live_event['league']['name'], live_event['type'])
                else: # type match
                    result += '{} {}\n'.format(live_event['league']['name'], live_event['blockName'])

                    # print team names
                    for team in live_event['match']['teams']:
                        result += '%s ' % team['name']
                    result+='\n'

        return result

    # make the region parameter optional
    def get_schedule(self,  region: Region = None):
        if region is None:
            region = self.region
        payload = {
            'hl': 'en-US',
            'leagueId': region.value
        }

        url = f'{self.api_base}/getSchedule'
        response = requests.get(url, params=payload, headers=self.headers)
        print(response)
        return response.json()

if __name__ == "__main__":
    lolesports = LolEsports(region=Region.LCS)
    print(lolesports.get_live())
    print(lolesports.get_schedule(Region.LCK)['data']['schedule']['events'][-1])