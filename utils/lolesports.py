# class Lolesports:
import os
import requests
from dotenv import load_dotenv
from enum import Enum

load_dotenv()
API_BASE = os.getenv('API_BASE')

class Region(Enum):
    LPL = 98767991314006698
    LCK = 98767991310872058
    LEC = 98767991302996019
    LCS = 98767991299243165
    PCS = 104366947889790212
    WORLDS = 98767975604431411

def get_live():
    result = ''
    payload = {
        'hl': 'en-US'
    }

    url = f'{API_BASE}/getLive'

    headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Referer': 'https://lolesports.com/',
                "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
            }
    response = requests.get(url, params=payload, headers=headers)
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


def get_schedule(region:Enum):
  payload = {
      'hl': 'en-US',
      'leagueId': region.value
  }

  url = f'{API_BASE}/getSchedule'

  headers = {
              'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
              'Referer': 'https://lolesports.com/',
              "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
          }
  response = requests.get(url, params=payload, headers=headers)
  print(response)
  return response.json()
