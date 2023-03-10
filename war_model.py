import numpy as np
from sklearn import linear_model
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

# read in the initial dataframes
pres_df = pd.read_csv('pres.csv', header=0).fillna(0)
demographics_df = pd.read_csv('demographics.csv', header=0).fillna(0)
results_df = pd.read_csv('results.csv', header=0).fillna(0)
shifts_df = pd.read_csv('20_22_shift.csv', header=0).fillna(0)
names_df = pd.read_csv('names.csv', header=0).fillna('None')
candidate_spending_df = pd.read_csv('candidate_spending.csv', header=0).fillna(0)
outside_spending_df = pd.read_csv('outside_spending.csv', header=0).fillna(0)

# convert strings to numbers, handle the commas in numbers. i know i can clean this up by doing it more efficiently but i'm tired.

for col in demographics_df.columns:
    if col != 'District':
        demographics_df[col] = demographics_df[col].map(lambda x: float(str(x).replace(',', '')))

for col in results_df.columns:
    if col != 'District':
        results_df[col] = results_df[col].map(lambda x: float(str(x).replace(',', '').replace('%', '')))

for col in candidate_spending_df.columns:
    if col != 'District':
        candidate_spending_df[col] = candidate_spending_df[col].map(lambda x: float(str(x).replace(',', '').replace('$', '')))

# preprocess presidential df to only have two way vote share and district name
pres_df['pres_20'] = (2 * (pres_df['Trump'])/(pres_df['Biden'] + pres_df['Trump']) - 1)
pres_df['pres_16'] = (2 * (pres_df['Trump16'])/(pres_df['Clinton'] + pres_df['Trump16']) - 1)

pres_df = pres_df[['District', 'pres_16', 'pres_20']]

# preprocess racial demographic data to be demographic percentages
baseline = 'Total Adult Population'

for col in demographics_df.columns:
    if col != baseline and col != 'District':
        demographics_df[col] = np.log2(100 * demographics_df[col] / demographics_df[baseline] + 1)
demographics_df = demographics_df.drop(columns=[baseline])

# merge the dataframes
full_data_df = demographics_df.merge(results_df, how='inner', left_on='District', right_on='District')
full_data_df = full_data_df.merge(pres_df, how='inner', left_on='District', right_on='District')
full_data_df = full_data_df.fillna(0)
full_data_df['State'] = full_data_df['District'].map(lambda x: x.split('-')[0])

# merge the dataframe with the shifts from 2020 to 2022
full_data_df = full_data_df.merge(shifts_df[['State', 'average_shift']], how='inner')
full_data_df['average_shift'] = full_data_df['average_shift'].map(lambda x: float(x.strip('%')) / 100)

# add in spending data
full_data_df = full_data_df.merge(candidate_spending_df, how='inner', left_on='District', right_on='District')
full_data_df = full_data_df.merge(outside_spending_df, how='inner', left_on='District', right_on='District')
full_data_df['dem_total_spent'] = full_data_df['dem_spend'] + full_data_df['dem_supported'] + full_data_df['gop_opposed']
full_data_df['gop_total_spent'] = full_data_df['rep_spend'] + full_data_df['gop_supported'] + full_data_df['dem_opposed']
spending_regularizer = 50000
full_data_df['spending_delta'] = np.log((spending_regularizer + full_data_df['gop_total_spent']) / (spending_regularizer + full_data_df['dem_total_spent']))

# which districts to ignore?
full_data_df['Uncontested'] = False
full_data_df.loc[(full_data_df['Dem'] == 0) | (full_data_df['Rep'] == 0), 'Uncontested'] = True
war_df = full_data_df[~full_data_df['Uncontested']]
war_df['Margin'] = 2 * full_data_df['Rep'] / (full_data_df['Dem'] + full_data_df['Rep']) - 1

# filtering for the model
X_cols = list(war_df.columns)
y_col = 'Margin'

# remove irrelevant columns from regression
cols_to_drop = [y_col, 'District', 'State', 'Dem', 'Rep', 'Total', 'Uncontested']
cols_to_drop += ['dem_total_spent', 'dem_spend', 'dem_raise', 'dem_supported', 'dem_opposed']
cols_to_drop += ['gop_total_spent', 'rep_spend', 'rep_raise', 'gop_supported', 'gop_opposed']

for col in cols_to_drop:
    X_cols.remove(col)

print(X_cols)
# modeling
model = linear_model.LinearRegression()
X = war_df[X_cols]
y = war_df[y_col]
model = model.fit(X, y)
residuals = y - model.predict(X)
war_df['WAR_raw'] = residuals

# if dem war is > dem margin
# elif rep war is > rep margin
war_df['generic_flip'] = False
war_df['battleground'] = False
war_df.loc[((war_df['WAR_raw'] > war_df[y_col]) & (war_df[y_col] > 0)), 'generic_flip'] = True
war_df.loc[((war_df['WAR_raw'] < war_df[y_col]) & (war_df[y_col] < 0)), 'generic_flip'] = True
war_df.loc[((war_df['pres_20'] > -0.145) & (war_df['pres_20'] < 0.055)), 'battleground'] = True

# formatting output, saving to csv
war_df['WAR'] = war_df['WAR_raw'].map(lambda x: f'R +{round(x * 100, 1)}' if x > 0 else f'D +{round(-x * 100, 1)}')
# drop the old margin before merging, use our two way one instead
full_data_df = full_data_df.drop(columns='Margin').merge(war_df[['District', 'WAR', 'WAR_raw', 'Margin', 'generic_flip', 'battleground']], how='left', left_on='District', right_on='District')
# merge with names
full_data_df = full_data_df.merge(names_df, how='inner')
full_data_df.to_csv('WAR Model 2022 FULL.csv', header=True)
full_data_df[['District', 'Democrat', 'Republican', 'WAR', 'WAR_raw', 'pres_16', 'pres_20', 'Margin', 'Incumbency', 'State', 'average_shift', 'generic_flip', 'battleground']].sort_values('WAR_raw').to_csv('WAR Model 2022 SKINNY.csv', header=True)
