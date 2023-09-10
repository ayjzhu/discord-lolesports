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
    def __init__(self, region: str = 'LEC', season: str = 'summer_2023'):
        self.api_base = os.getenv('API_BASE')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Referer': 'https://lolesports.com/',
            "x-api-key": os.getenv('X_API_KEY')
        }
        self.league = Region[region.upper()]
        self.league_id = self.league.value
        self.timeframe = season
        # self.teams = self.get_teams_mapping(self.tournaments_ids)

    # an alternative constructor for passing in league id as an int
    @classmethod
    def from_league_id(cls, league_id: int):
        """Alternative constructor for passing in league id as an int

        Parameters
        ----------
        league_id: `int`
            The league id to get the tournaments from

        Returns
        -------
        cls: `LolEsports`
            An instance of the class

        Raises
        ------
        ValueError
            If the input league id is not in the Region enum class
        """
        if league_id not in [region.value for region in Region]:
            raise ValueError(f'Invalid league id. Expected one of {Region.__members__.keys()}')
        else:
            league = Region(league_id)
            return cls(league.name)

    def get_league_id(self) -> int:
        """Get the league id

        Returns
        -------
        league_id: `int`
            The league id
        ---
        """
        return self.league_id

    # create a get_current_tournament_id function which only has an optional timeframe to get the tournament id
    def get_current_tournament_id(self, timeframe:str = None) -> int:
        """Get the current tournament id

        Parameters
        ----------
        timeframe: `str`
            The timeframe to extract the tournaments from

        Returns
        -------
        tournament_id: `int`
            The current tournament id
        ---
        """
        # set default timeframe to current timeframe if not provided
        if timeframe is None:
            timeframe = self.timeframe

        # get the tournaments
        tournaments = self.get_tournaments(self.league_id)
        # get the tournaments for the timeframe
        matching_tournaments = self.extract_tournaments_by_timeframe(tournaments, timeframe)
        # get the matching ids
        matching_ids = self.extract_tournament_ids(matching_tournaments)
        # get the current tournament id
        return matching_ids[0]
    

    # create a get_current_standings function which only needs the timeframe to get the standings
    def get_current_standings(self, timeframe:str = None) -> List[dict]:
        """Get the standings of a tournament

        Parameters
        ----------
        timeframe: `str`
            The timeframe to extract the tournaments from
            
        Returns
        -------
        rankings: `list` of `dict`
            A list of standings for each tournament
        ---
        """
        print(timeframe)
        # set default timeframe to current timeframe if not provided
        if timeframe is None:
            timeframe = self.timeframe

        # get the tournaments
        tournaments = self.get_tournaments(self.league_id)
        # get the tournaments for the timeframe
        matching_tournaments = self.extract_tournaments_by_timeframe(tournaments, timeframe)
        # get the matching ids
        matching_ids = self.extract_tournament_ids(matching_tournaments)
        # get the standings
        rankings = self.get_standings(matching_ids)
        return rankings

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
        print(response, response.url.split('/')[-1])   # print the url slug and the response code
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
        print(response, response.url.split('/')[-1])   # print the url slug and the response code

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
        print(response, response.url.split('/')[-1])   # print the url slug and the response code
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
            The league_id(s) to get the tournaments from.

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
        print(response, response.url.split('/')[-1])   # print the url slug and the response code
        tournaments_data = response.json()['data']['leagues']
        return tournaments_data

    # create a helper function to extract tournaments by timeframe
    @staticmethod
    def extract_tournaments_by_timeframe(tournaments_data: list, timeframe: str) -> list:
        """ A staic helper to extract tournaments by timeframe

        Parameters
        ----------
        tournaments_data: `list`
            A list of esports tournaments
        timeframe: `str`
            The timeframe to extract the tournaments from

        Returns
        -------
        matching_tournaments: `list`
            A list of tournaments that match the timeframe
        """
        matching_tournaments = []

        for item in tournaments_data:
            tournaments = item.get('tournaments', [])
            for tournament in tournaments:
                slug = tournament.get('slug', '')
                if timeframe in slug:
                    matching_tournaments.append(tournament)

        return matching_tournaments
    
    # create a staic helper function to extract tournaments ids in a list of tournaments
    # the tournaments can be two types of either a list of tournaments or a list of matching tournaments
    @staticmethod
    def extract_tournament_ids(tournaments: list) -> list:
        """ A static helper to extract tournaments ids in a list of tournaments

        Parameters
        ----------
        tournaments: `list`
            A list of esports tournaments

        Returns
        -------
        tournament_ids: `list`
            A list of tournaments ids
        ---
        """
        tournament_ids = []
        for tournament in tournaments:
            if 'tournaments' in tournament.keys(): 
                tournament_ids += [int(tournament['id']) for tournament in tournament['tournaments']]
            else:
                tournament_ids.append(int(tournament['id'])) 
        return tournament_ids
    

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
        print(response, response.url.split('/')[-1])   # print the url slug and the response code
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
            The league_id(s) to get the tournaments from.
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
        matching_tournaments = self.extract_tournaments_by_timeframe(tournaments, timeframe)
        # get the matching ids
        matching_ids = self.extract_tournament_ids(matching_tournaments)
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
    @staticmethod
    def get_major_league_ids() -> list:
        """ A helper to get the major league ids from the constants file which are the first 4 items in the Region(Enum)

        Returns
        -------
        major_league_ids: `list`
            A list of major league ids
        """
        major_league_ids = [region.value for region in Region][:4]
        return major_league_ids

    def get_teams_mapping(self, tournament_ids: Union[int, List[int]], to_sort: bool = False) -> dict:
        """Get the teams mapping from the current league

        Parameters
        ----------
        tournament_ids: `int` or `list` of `int`
            The tournament_id(s) to get the teams mapping from.
        to_sort: `bool`
            Whether to sort the teams mapping alphabetically

        Returns
        -------
        teams: `dict`
            A dictionary of teams with the code as the key and the slug as the value sorted alphabetically if to_sort is True
        """
        if isinstance(tournament_ids, int):
            tournament_ids = [tournament_ids]
        standings = []
        for tournament_id in tournament_ids:
            standings.extend(self.get_standings(tournament_id))
        teams = {}
        # Iterate through the list and extract the code-to-slug mapping
        for standing in standings:
            for tournament_name, teams_list in standing.items():
                for team_info in teams_list:
                    for team in team_info['teams']: # loop once since only one team
                        code = team['code']
                        slug = team['slug']
                        teams[code.lower()] = slug

        if to_sort:
            # sort the code-to-slug mapping alphabetically
            teams = dict(sorted(teams.items()))

        return teams

    # create a helper static function to get the teams mapping from the given league(s)
    @staticmethod
    def get_teams_mapping_from_leagues(league_ids: Union[int, List[int]], to_sort: bool = False) -> dict:
        """ A static helper to get the teams mapping from the given league(s)

        Parameters
        ----------
        league_ids: `int` or `list` of `int`
            The league_id(s) to get the teams mapping from.
        to_sort: `bool`
            Whether to sort the teams mapping alphabetically

        Returns
        -------
        teams: `dict`
            A dictionary of teams with the code as the key and the slug as the value sorted alphabetically if to_sort is True
        """
        if isinstance(league_ids, int):
            league_ids = [league_ids]
        teams = {}
        for league_id in league_ids:
            lolesports = LolEsports.from_league_id(league_id)
            teams.update(lolesports.get_teams_mapping(lolesports.get_current_tournament_id(), to_sort))
        return teams

    # create a function to exact teams from the current league
    def get_current_teams(self) -> dict:
        """Get the teams from the current league

        Returns
        -------
        teams: `dict`
            A dictionary of teams with the code as the key and the slug as the value
        """
        current_tournament_id = self.get_current_tournament_id()
        teams = self.get_teams_mapping(current_tournament_id)
        return teams

if __name__ == "__main__":
    lolesports = LolEsports('lec')
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

    # test get_tournaments, extract_tournaments_by_timeframe, and get_standings
    # major_regions_ids = lolesports._get_major_league_ids()
    # timeframe = "summer_2023"
    #test display_standings
    # lolesports.display_standings(major_regions_ids, timeframe, to_str=False)

    # # get current standings
    # standings = lolesports.get_current_standings()
    # print(standings)

    # test static helper function extract_tournament_ids
    # tournaments = lolesports.get_tournaments(Region.LPL.value)
    # matching_tournaments = lolesports.extract_tournaments_by_timeframe(tournaments, 'summer_2023')
    # tournament_ids = LolEsports.extract_tournament_ids(matching_tournaments)
    # print(tournament_ids)

    # # test get_current_tournament_id
    # print(lolesports.get_current_tournament_id())

    # test get_teams_mapping
    teams = lolesports.get_current_teams()
    print(teams)

    # test get_teams_mapping_from_leagues
    teams = lolesports.get_teams_mapping_from_leagues([Region.LCK.value, Region.LCS.value])
    print(teams)
