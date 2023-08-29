import os
import requests
from dotenv import load_dotenv
from enum import Enum
import pandas as pd

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

    def get_live(self) -> str:
        '''Get the live events

        Returns
        -------
        result: `str`
            The live events
        ---
        '''
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
    def get_schedule(self,  region: Region = None) -> dict:
        '''Get the schedule of upcoming events

        Parameters
        ----------
        region: :class:`Region`
            The region to get the schedule for. Defaults to LEC

        Returns
        -------
        schedule: `dict`
            The schedule of upcoming events
        ---
        '''
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

    # create a get esports league function
    def get_leagues(self, is_sorted: bool = False) -> list: 
        """Get all the esports leagues

        Parameters
        ----------
        is_sorted: `bool`
            Whether to sort the leagues by priority

        Returns
        -------
        leagues: `list`
            A list of esports leagues
        ---
        """
        payload = {
            'hl': 'en-US'
        }
        url = f'{self.api_base}/getLeagues'
        response = requests.get(url, params=payload, headers=self.headers)
        print(response)
        try:
            leagues = response.json()['data']['leagues'] # raw leagues data
            df = pd.DataFrame(leagues)
            if is_sorted:
                sorted_df = df.sort_values(by=['priority']).reset_index(drop=True)

                # further sort the leagues to bring the 2 semi major leagues to the top
                insert_index = len(df.loc[df['priority'] < 202])    # insert below the 4 major leagues
                # Find the index of the row with "VCS" in the name column
                vcs_index = sorted_df[sorted_df['name'] == 'VCS'].index[0]
                # Extract the row with "VCS" and "PCS" (the row below it)
                rows_to_move = sorted_df.loc[vcs_index:vcs_index+1]
                # Delete the rows from their original positions
                sorted_df = sorted_df.drop(rows_to_move.index)
                # Insert the rows at index 4
                sorted_df = pd.concat([sorted_df.iloc[:insert_index], rows_to_move, sorted_df.iloc[insert_index:]], ignore_index=True)
                # convert the dataframe to a list of dictionaries 
                leagues = sorted_df.to_dict(orient='records')
        except Exception as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            return None
        else:
            return leagues
    
    # create a helper function to process the league data and get the sub leagues
    def get_sub_leagues(self, leagues: list) -> tuple:
        """ A helper to process the leagues data and sort them into various sub leagues

        Parameters
        ----------
        leagues: `list`
            A list of esports leagues

        Returns
        -------
        sub_leagues: `tuple`
            A tuple of sub leagues :attr:`list` in the following order: major_leagues, popular_leagues, primary_leagues
        ---
        """
        # leagues = self.get_leagues(is_sorted=True)
        leagues_df = pd.DataFrame(leagues)
        if leagues is None:
            return None
        try:
            # Find the index of the row with "VCS" in the name column
            vcs_index = leagues_df[leagues_df['name'] == 'VCS'].index[0]
            # Extract the row with "VCS" and "PCS" (the row below it)
            semi_leagues = leagues_df.loc[vcs_index:vcs_index+1]
            # 9 minor_leagues & international: TCL, CBLOL, LLA, LCO, LJL, LCL, WORLDS, MSI, ALL_STAR_EVENT
            minor_leagues = leagues_df.loc[(leagues_df['priority'] < 1000) & (leagues_df['priority'] > 201)]

            # processed leagues data
            # 4 major leagues: LCS, LEC, LCK, LPL
            major_leagues = leagues_df.loc[leagues_df['priority'] < 202]
            # 6 popular leagues: LCS, LEC, LCK, LPL, PCS, VCS
            popular_leagues = pd.concat([major_leagues, semi_leagues], ignore_index=True)
            # 15 primary leagues: LCS, LEC, LCK, LPL, PCS, VCS, TCL, CBLOL, LLA, LCO, LJL, LCL, WORLDS, MSI, ALL_STAR_EVENT
            primary_leagues = pd.concat([major_leagues, semi_leagues, minor_leagues], ignore_index=True)
        except Exception as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            return None
        else:
            return major_leagues.to_dict(orient='records'), popular_leagues.to_dict(orient='records'), primary_leagues.to_dict(orient='records')

if __name__ == "__main__":
    lolesports = LolEsports(region=Region.LCS)
    # print(lolesports.get_live())
    # print(lolesports.get_schedule(Region.LCK)['data']['schedule']['events'][-1])
    ## print the first 16 leagues by name
    # leagues = lolesports.get_leagues(is_sorted=True)
    # for league in leagues[:16]:
    #     print(league['name'])
    sub_leagues = lolesports.get_sub_leagues(lolesports.get_leagues(is_sorted=True))[0]
    # print the major, popular and pirmary leagues by name
    for league in sub_leagues:
        print(league['name'])
    
