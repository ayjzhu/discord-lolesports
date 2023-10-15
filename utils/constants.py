from enum import Enum

# icon url constants
ICONS = {
    'lolesports_teal' : r"https://am-a.akamaihd.net/image?resize=140:&f=http%3A%2F%2Fstatic.lolesports.com%2Fteams%2F1681281407829_LOLESPORTSICON.png",
    'riot' : 'https://static.developer.riotgames.com/img/logo.png',
    'worlds' : 'http://static.lolesports.com/leagues/1592594612171_WorldsDarkBG.png',
    'lolesports' : 'https://static.lolesports.com/leagues/1693555886600_lolesports_icon_ice-01.png',
}

# contains all the popular regions
class Region(Enum):
    LCS = 98767991299243165
    LEC = 98767991302996019
    LCK = 98767991310872058
    LPL = 98767991314006698
    VCS = 107213827295848783
    PCS = 104366947889790212    
    TCL = 98767991343597634
    CBLOL = 98767991332355509
    LLA = 101382741235120470
    LCO = 105709090213554609
    LJL = 98767991349978712
    LCL = 98767991355908944
    WORLDS = 98767975604431411
    MSI = 98767991325878492
    WQS = 110988878756156222

class RegionStr(Enum):
    LPL = '98767991314006698'
    LCK = '98767991310872058'
    LEC = '98767991302996019'
    LCS = '98767991299243165'
    PCS = '104366947889790212'
    WORLDS = '98767975604431411'
    MSI = '98767991325878492'
    WQS = '110988878756156222'
    INTL = '98767975604431411, 98767991325878492, 110988878756156222'


# contains all the regions and their respective ids
class AllRegion(Enum):
    LCS = 98767991299243165
    LEC = 98767991302996019
    LCK = 98767991310872058
    LPL = 98767991314006698
    TCL = 98767991343597634
    CBLOL = 98767991332355509
    LLA = 101382741235120470
    LCO = 105709090213554609
    LJL = 98767991349978712
    LCL = 98767991355908944
    WORLDS = 98767975604431411
    MSI = 98767991325878492
    ALL_STAR_EVENT = 98767991295297326
    HITPOINT_MASTERS = 105266106309666619
    ESPORTS_BALKAN_LEAGUE = 105266111679554379
    GREEK_LEGENDS_LEAGUE = 105266108767593290
    ARABIAN_LEAGUE = 109545772895506419
    LCK_ACADEMY = 108203770023880322
    LCK_CHALLENGERS = 98767991335774713
    LJL_ACADEMY = 106827757669296909
    PRIME_LEAGUE = 105266091639104326
    NORTH_REGIONAL_LEAGUE = 110371976858004491
    CBLOL_ACADEMY = 105549980953490846
    SUPERLIGA = 105266074488398661
    EMEA_MASTERS = 100695891328981122
    PG_NATIONALS = 105266094998946936
    LIGA_PORTUGUESA = 105266101075764040
    ELITE_SERIES = 107407335299756365
    NLC = 105266098308571975
    LA_LIGUE_FRANCAISE = 105266103462388553
    SOUTH_REGIONAL_LEAGUE = 110372322609949919
    VCS = 107213827295848783
    PCS = 104366947889790212
    COLLEGE_CHAMPIONSHIP = 107898214974993351
    LCS_CHALLENGERS_QUALIFIERS = 109518549825754242
    LCS_CHALLENGERS = 109511549831443335
    ULTRALIGA = 105266088231437431
    TFT_RISING_LEGENDS = 108001239847565215

MAJOR_TEAMS = {'g2': 'g2-esports', 'fnc': 'fnatic', 'xl': 'excel', 'th': 'team-heretics-lec', 'bds': 'team-bds', 'sk': 'sk-gaming', 'mad': 'mad-lions', 'koi': 'rogue', 'ast': 'astralis', 'vit': 'team-vitality', 'kt': 'kt-rolster', 'gen': 'geng', 'hle': 'hanwha-life-esports', 'dk': 'dwg-kia', 't1': 't1', 'drx': 'drx', 'lsb': 'liiv-sandbox', 'bro': 'fredit-brion', 'ns': 'nongshim-redforce', 'kdf': 'kwangdong-freecs', 'c9': 'cloud9', 'gg': 'golden-guardians', 'eg': 'evil-geniuses', 'tl': 'team-liquid', 'nrg': 'nrg-esports', 'tsm': 'tsm', 'dig': 'dignitas', '100': '100-thieves', 'fly': 'flyquest', 'imt': 'immortals-progressive', 'blg': 'bilibili-gaming', 'jdg': 'jd-gaming', 'lng': 'lng-esports', 'tes': 'top-esports', 'omg': 'oh-my-god', 'wbg': 'weibo-gaming', 'rng': 'royal-never-give-up', 'edg': 'edward-gaming', 'we': 'team-we', 'nip': 'victory-five', 'fpx': 'funplus-phoenix', 
'ig': 'invictus-gaming', 'tt': 'thunder-talk-gaming', 'up': 'ultra-prime', 'ra': 'rare-atom', 'al': 'anyones-legend', 'lgd': 'lgd-gaming'}

WORLDS_TEAMS = {
    'jdg': 'jd-gaming',
    'blg': 'bilibili-gaming',
    'lng': 'lng-esports',
    'wbg': 'weibo-gaming',
    'gen': 'geng',
    't1': 't1',
    'kt': 'kt-rolster',
    'dk': 'dwg-kia',
    'nrg': 'nrg-esports',
    'c9': 'cloud9',
    'tl': 'team-liquid',
    'g2': 'g2-esports',
    'fnc': 'fnatic',
    'mad': 'mad-lions',
    'bds': 'team-bds',
    'psg': 'psg-talon',
    'cfo': 'ctbc-flying-oyster',
    'gam': 'gam-esports',
    'tw': 'team-whales',
}