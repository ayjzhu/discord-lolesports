import os
import requests
from dotenv import load_dotenv
from enum import Enum
import pandas as pd
from typing import Optional, Union, List 
# from constants import Region
load_dotenv()
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
        self.region = region
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Referer': 'https://lolesports.com/',
            "x-api-key": os.getenv('X_API_KEY')
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
    def _get_sub_leagues(self, leagues: list) -> tuple:
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
            # 15 primary leagues: LCS, LEC, LCK, LPL, PCS, VCS, TCL, CBLOL, LLA, LCO, LJL, LCL, WORLDS, MSI, ALL_STAR_EVENT, WQS
            wqs = leagues_df[leagues_df['slug'] == 'wqs'] # world qualifier series
            primary_leagues = pd.concat([major_leagues, semi_leagues, minor_leagues, wqs], ignore_index=True)
        except Exception as e:
            print(f'**`ERROR:`** {type(e).__name__} - {e}')
            return None
        else:
            return major_leagues.to_dict(orient='records'), popular_leagues.to_dict(orient='records'), primary_leagues.to_dict(orient='records')

    def get_tournaments(self, league_ids: Union[int, List[int]]) -> dict:
        """Get all the esports tournaments from a region

        Parameters
        ----------
        league_ids: `int` or `list` of `int`
            The region_id(s) to get the tournaments from.

        Returns
        -------
        tournaments: `dict`
            A dictionary of esports tournaments
        ---
        """
        if isinstance(league_ids, int):
            regions_ids = [league_ids]  # Convert a single league_id to a list
        elif isinstance(league_ids, list):
            regions_ids = league_ids  # Use the provided list of league_ids
        else:
            raise ValueError("Invalid parameter type. Expected int or list of int.")

        payload = {
            'hl': 'en-US',
            'leagueId': ','.join(map(str, regions_ids))
        }
        url = f'{self.api_base}/getTournamentsForLeague'
        response = requests.get(url, params=payload, headers=self.headers)
        print(response)
        print(response.url)
        return response.json()

    # create a helper function to extract tournaments by timeframe
    def _extract_tournaments_by_timeframe(self, data: dict, timeframe: str) -> list:
        """ A helper to extract tournaments by timeframe

        Parameters
        ----------
        data: `dict`
            A dictionary of esports tournaments
        timeframe: `str`
            The timeframe to extract the tournaments from

        Returns
        -------
        matching_tournaments: `list`
            A list of tournaments that match the timeframe
        ---
        """
        matching_tournaments = []
        tournaments_data = data['data']['leagues']

        for item in tournaments_data:
            tournaments = item.get('tournaments', [])
            for tournament in tournaments:
                slug = tournament.get('slug', '')
                if timeframe in slug:
                    matching_tournaments.append(tournament)

        return matching_tournaments

    def get_standings(self, tournament_id: Union[int, List[int]]) -> List[dict]:
        """Get the standings of a tournament

        Parameters
        ----------
        tournament_id: `int` or `list` of `int`
            The tournament_id(s) to get the standings from.

        Returns
        -------
        rankings: `list` of `dict`
            A list of standings for each tournament
        ---
        """
        if isinstance(tournament_id, int):
            tournament_id = [tournament_id]  # Convert a single league_id to a list
        elif isinstance(tournament_id, list):
            pass  # Use the provided list of league_ids
        else:
            raise ValueError("Invalid parameter type. Expected int or list of int.")
        payload = {
            'hl': 'en-US',
            'tournamentId' : ','.join(map(str, tournament_id)),
        }
        url = f'{self.api_base}/getStandingsV3'
        response = requests.get(url, params=payload, headers=self.headers)
        print(response)
        standings = response.json()['data']['standings']
        rankings = []
        for standing in standings:
            slugs = standing['slug'].split('_')   # get the season name to use as key
            season = ' '.join(slug.capitalize() for slug in slugs)
            stages = standing['stages']                    # only regular season has rankings
            ranking = stages[0]['sections'][0]['rankings'] # stage 0: regular season; only 1 section
            rankings.append({season:ranking})
        return rankings

    def display_standings(self, league_ids: Union[int, List[int]], timeframe: str, to_str: bool = False) -> Optional[str]:
        """Display the standings of a tournament
        
        Parameters
        ----------
        league_ids: `int` or `list` of `int`
            The region_id(s) to get the tournaments from.
        timeframe: `str`
            The timeframe to extract the tournaments from
        to_str: `bool`
            Whether to return the standings as a string or print it

        Returns
        -------
        standings_str: `str`
            The standings as a string
        ---
        """
        # this function calls get_tournaments, extract_tournaments_by_timeframe, get_standings and then display the standings
        # get the tournaments
        tournaments = self.get_tournaments(league_ids)
        # get the tournaments for the timeframe
        matching_tournaments = self._extract_tournaments_by_timeframe(tournaments, timeframe)
        # get the matching ids
        matching_ids = [tournament['id'] for tournament in matching_tournaments]
        # get the standings
        standings = self.get_standings(matching_ids)
        # display the standings
        standings_str = ""
        for standing in standings:
            for standing_name, rankings in standing.items():
                standings_str += f"\n{standing_name}:"
                for ranking in rankings:    # ranking within each league
                    ordinal = ranking['ordinal']
                    team = ranking['teams'][0] # only one team per slot
                    name = team['name']
                    code = team['code']
                    wins = team['record']['wins']
                    losses = team['record']['losses']
                    standings_str += f"\n{ordinal}. {name} ({code}): {wins}-{losses}"
            standings_str += "\n"
        if to_str:
            return standings_str
        else:
            print(standings_str)
    
    # create a helper function to get the major league ids from the constants file which are the first 4 items in the Region(Enum)
    def _get_major_league_ids(self) -> list:
        """ A helper to get the major league ids from the constants file which are the first 4 items in the Region(Enum)

        Returns
        -------
        major_league_ids: `list`
            A list of major league ids
        ---
        """
        major_league_ids = [region.value for region in Region][:4]
        return major_league_ids

if __name__ == "__main__":
    lolesports = LolEsports(region=Region.LCS)
    # # test get_live
    # print(lolesports.get_live())
    # # test get_schedule
    # print(lolesports.get_schedule(Region.LCK)['data']['schedule']['events'][-1])
    # # test get_leagues
    # # print the first 16 leagues by name
    # leagues = lolesports.get_leagues(is_sorted=True)
    # for league in leagues[:16]:
    #     print(league['name'])
    # # test get_sub_leagues
    # sub_leagues = lolesports.get_sub_leagues(lolesports.get_leagues(is_sorted=True))[0]
    # for league in sub_leagues:
    #     print(league['name'])   # print the major, popular and pirmary leagues by name

    # test get_tournaments, _extract_tournaments_by_timeframe, and get_standings
    major_regions_ids = lolesports._get_major_league_ids()
    timeframe = "summer_2023"
    # test display_standings
    lolesports.display_standings(major_regions_ids, timeframe, to_str=False)
