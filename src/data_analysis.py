import numpy as np
import zipfile
import os
import sqlite3
import pandas as pd

zip_ref = zipfile.ZipFile('../data/database.sqlite.zip', 'r')
zip_ref.extractall('../data')
zip_ref.close()

conn = sqlite3.connect('../data/database.sqlite')

df = pd.read_sql_query("SELECT * FROM Country;", conn)


conn.close()
os.remove('../data/database.sqlite')
