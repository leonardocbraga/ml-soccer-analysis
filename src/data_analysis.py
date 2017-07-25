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

player_df = pd.read_sql_query("SELECT * FROM Player;", conn)
match_df = pd.read_sql_query("SELECT * FROM Match;", conn)
player_att_df = pd.read_sql_query("SELECT * FROM Player_Attributes;", conn)

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

# wins
team_df = pd.read_sql_query("SELECT * FROM Team;", conn)

team_att_df = pd.read_sql_query("SELECT * FROM Team_Attributes;", conn)


match_df['home_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] > row['away_team_goal'] else 0, axis = 1)
match_df['away_win'] = match_df.apply(lambda row: 1 if row['home_team_goal'] < row['away_team_goal'] else 0, axis = 1)
home_winners = match_df.groupby('home_team_api_id')['home_win'].sum()
away_winners = match_df.groupby('away_team_api_id')['away_win'].sum()

team_att_df['n_win'] = team_att_df['team_api_id'].apply(lambda team_id: home_winners[team_id] + away_winners[team_id])


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
