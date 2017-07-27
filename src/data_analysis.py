import numpy as np
import zipfile
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os.path

DATA_PATH = '../data/'
DB_NAME = 'database.sqlite'
DB_NAME_ZIP = 'database.sqlite.zip'

file_name = DATA_PATH + DB_NAME
if not os.path.isfile(file_name):
    zip_ref = zipfile.ZipFile(DATA_PATH + DB_NAME_ZIP, 'r')
    zip_ref.extractall(DATA_PATH)
    zip_ref.close()

conn = sqlite3.connect(file_name)

# loading dataframes
player_df = pd.read_sql_query("SELECT * FROM Player;", conn)
match_df = pd.read_sql_query("SELECT * FROM Match;", conn)
player_att_df = pd.read_sql_query("SELECT * FROM Player_Attributes;", conn)
team_df = pd.read_sql_query("SELECT * FROM Team;", conn)
team_att_df = pd.read_sql_query("SELECT * FROM Team_Attributes;", conn)

match_df = pre_process_rating(match_df, player_df, player_att_df)
pre_process_win(match_df)

home_wins = match_df[match_df['home_win'] == 1]
away_wins = match_df[match_df['away_win'] == 1]
plt.plot(away_wins['home_rating'], away_wins['away_rating'], 'bs', home_wins['home_rating'], home_wins['away_rating'], 'r8', markersize=4)
#plt.axis([70, 80, 70, 80])
plt.xlabel('Home')
plt.ylabel('Away')
plt.tight_layout()
plt.show()

anomalies = away_wins[away_wins['away_rating'] - away_wins['home_rating'] < -10]
home_team = team_df[team_df['team_api_id'] == 8634]
away_team = team_df[team_df['team_api_id'] == 9864]


team_df['shooting'] = team_df['team_api_id'].apply(lambda team_id: team_att_df[team_att_df['team_api_id'] == team_id]['chanceCreationShooting'].mean())
team_df['defence'] = team_df['team_api_id'].apply(lambda team_id: team_att_df[team_att_df['team_api_id'] == team_id]['defenceAggression'].mean())
team_df = team_df.dropna(subset=['shooting'])
team_df = team_df.dropna(subset=['defence'])


# player analysis

player_df.sort_values('rating')

conn.close()
os.remove(DATA_PATH + DB_NAME)

def pre_process_rating(match_df, player_df, player_att_df):
    # extracting mean rating for each player and creating a dict
    player_df['rating'] = player_df['player_api_id'].apply(lambda player_id: player_att_df[player_att_df['player_api_id'] == player_id]['overall_rating'].mean())
    ratings_dict = dict([(id, rating) for id, rating in zip(player_df.player_api_id, player_df.rating)])

    home_player_cols = ['home_player_' + str(i) for i in xrange(1, 12)]
    away_player_cols = ['away_player_' + str(i) for i in xrange(1, 12)]
    player_cols = home_player_cols + away_player_cols

    home_rating_cols = ['home_rating_' + str(i) for i in xrange(1, 12)]
    away_rating_cols = ['away_rating_' + str(i) for i in xrange(1, 12)]
    rating_cols = home_rating_cols + away_rating_cols

    match_df = match_df.dropna(subset=player_cols)
    match_df[rating_cols] = match_df[player_cols].apply(lambda row: row.apply(lambda pid: ratings_dict[pid]))
    match_df['home_rating'] = match_df[home_rating_cols].mean(axis = 1)
    match_df['away_rating'] = match_df[away_rating_cols].mean(axis = 1)
    return match_df

def pre_process_win(match_df):
    # wins
    match_df['home_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] > row['away_team_goal'] else 0, axis = 1)
    match_df['away_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] < row['away_team_goal'] else 0, axis = 1)

def plot_win_rating():
    home_winners = match_df.groupby('home_team_api_id').agg({'home_win': np.sum, 'home_rating': np.mean}) #['home_win'].sum()
    away_winners = match_df.groupby('away_team_api_id').agg({'away_win': np.sum, 'away_rating': np.mean}) #['away_win'].sum()
    team_df['n_win'] = team_df['team_api_id'].apply(lambda team_id: home_winners.loc[team_id]['home_win'] + away_winners.loc[team_id]['away_win'] if team_id in home_winners.index else np.nan)
    team_df['rating'] = team_df['team_api_id'].apply(lambda team_id: np.mean([home_winners.loc[team_id]['home_rating'], away_winners.loc[team_id]['away_rating']]) if team_id in home_winners.index else np.nan)

    team_df = team_df.dropna(subset=['n_win'])

    plot_series = team_df.sort_values('n_win')
    plt.plot(plot_series['n_win'], plot_series['rating'], linewidth=2)
    plt.xlabel('Wins')
    plt.ylabel('Shooting')
    plt.tight_layout()
    plt.show()
