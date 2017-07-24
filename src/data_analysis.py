import numpy as np
import zipfile
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = '../data/'
DB_NAME = 'database.sqlite'
DB_NAME_ZIP = 'database.sqlite.zip'

zip_ref = zipfile.ZipFile(DATA_PATH + DB_NAME_ZIP, 'r')
zip_ref.extractall(DATA_PATH)
zip_ref.close()

conn = sqlite3.connect(DATA_PATH + DB_NAME)

player_df = pd.read_sql_query("SELECT * FROM Player;", conn)

player_att_df = pd.read_sql_query("SELECT * FROM Player_Attributes;", conn)
player_df['rating'] = player_df['player_api_id'].apply(lambda player_id: player_att_df[player_att_df['player_api_id'] == player_id]['overall_rating'].mean())

team_df = pd.read_sql_query("SELECT * FROM Team;", conn)

team_att_df = pd.read_sql_query("SELECT * FROM Team_Attributes;", conn)

match_df = pd.read_sql_query("SELECT * FROM Match;", conn)
match_df['home_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] > row['away_team_goal'] else 0, axis = 1)
match_df['away_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] < row['away_team_goal'] else 0, axis = 1)
home_winners = match_df.groupby('home_team_api_id')['home_win'].sum()
away_winners = match_df.groupby('away_team_api_id')['away_win'].sum()

team_att_df['n_win'] = team_att_df['team_api_id'].apply(lambda team_id: home_winners[team_id] + away_winners[team_id])

home_player_cols = []
away_player_cols = []
for i in xrange(1, 12):
    home_player_cols.append('home_player_' + str(i))
    away_player_cols.append('away_player_' + str(i))

match_df = match_df.dropna(subset=home_player_cols)
match_df[home_player_cols].apply(lambda row: player_df[player_df['player_api_id'] == row]['rating'])
match_df[home_player_cols].mean(axis = 1)


# test
team_att_df[team_att_df['team_api_id'] == 8650]['n_win']
match_df[match_df['home_team_api_id'] == 8650][['home_win', 'home_team_goal', 'away_team_goal']]

#team_df = team_att_df.groupby('team_api_id')['n_win'].mean()

team_df['n_win'] = team_df['team_api_id'].apply(lambda team_id: team_att_df[team_att_df['team_api_id'] == team_id]['n_win'].mean())
team_df['shooting'] = team_df['team_api_id'].apply(lambda team_id: team_att_df[team_att_df['team_api_id'] == team_id]['chanceCreationShooting'].mean())
team_df['defence'] = team_df['team_api_id'].apply(lambda team_id: team_att_df[team_att_df['team_api_id'] == team_id]['defenceAggression'].mean())
team_df = team_df.dropna(subset=['shooting'])
team_df = team_df.dropna(subset=['defence'])

plot_series = team_df.sort_values('n_win')

plt.plot(plot_series['n_win'], plot_series['shooting'], linewidth=2)
plt.plot(plot_series['n_win'], plot_series['defence'], linewidth=2)
plt.xlabel('Wins')
plt.ylabel('Shooting')
plt.tight_layout()
plt.show()


# player analysis

player_df.sort_values('rating')

conn.close()
os.remove(DATA_PATH + DB_NAME)
