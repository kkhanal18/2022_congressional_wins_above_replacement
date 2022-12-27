import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model

# read in the initial dataframes
pres_df = pd.read_csv('pres.csv', header=0).fillna(0)
demographics_df = pd.read_csv('demographics.csv', header=0).fillna(0)
results_df = pd.read_csv('results.csv', header=0).fillna(0)
shifts_df = pd.read_csv('20_22_shift.csv', header=0).fillna(0)
names = pd.read_csv('names.csv', header=0).fillna('None')

# convert strings to numbers, handle the commas in numbers
for col in pres_df.columns:
    if col != 'District':
        pres_df[col] = pres_df[col].map(lambda x: float(str(x).replace(',', '')))

for col in demographics_df.columns:
    if col != 'District':
        demographics_df[col] = demographics_df[col].map(lambda x: float(str(x).replace(',', '')))

for col in results_df.columns:
    if col != 'District':
        results_df[col] = results_df[col].map(lambda x: float(str(x).replace(',', '').replace('%', '')))

# preprocess presidential df to only have two way vote share and district name
pres_df['pres_20'] = (2 * (pres_df['Trump'])/(pres_df['Biden'] + pres_df['Trump']) - 1)
pres_df['pres_16'] = (2 * (pres_df['Trump16'])/(pres_df['Clinton'] + pres_df['Trump16']) - 1)

pres_df = pres_df[['District', 'pres_16', 'pres_20']]

# preprocess racial demographic data to be demographic percentages
baseline = 'Total Adult Population'

for col in demographics_df.columns:
    if col != baseline and col != 'District':
        demographics_df[col] = np.log(100 * demographics_df[col] / demographics_df[baseline] + 1)
demographics_df = demographics_df.drop(columns=[baseline])

# merge the dataframes
full_data_df = demographics_df.merge(results_df, how='inner', left_on='District', right_on='District')
full_data_df = full_data_df.merge(pres_df, how='inner', left_on='District', right_on='District')
full_data_df = full_data_df.fillna(0)
full_data_df['State'] = full_data_df['District'].map(lambda x: x.split('-')[0])

# merge the dataframe with the shifts from 2020 to 2022
full_data_df = full_data_df.merge(shifts_df[['State', 'Shift']], how='inner')
full_data_df['Shift'] = full_data_df['Shift'].map(lambda x: float(x.strip('%')) / 100)

# which districts to ignore?
full_data_df['Uncontested'] = False
full_data_df.loc[(full_data_df['Dem'] == 0) | (full_data_df['Rep'] == 0), 'Uncontested'] = True
war_df = full_data_df[~full_data_df['Uncontested']]
war_df['Margin'] = 2 * full_data_df['Rep'] / (full_data_df['Dem'] + full_data_df['Rep']) - 1

# filtering for the model
X_cols = list(war_df.columns)
y_col = 'Margin'

# remove irrelevant columns from regression
for col in [y_col, 'District', 'State', 'Dem', 'Rep', 'Total', 'Uncontested']:
    X_cols.remove(col)

# modeling
model = linear_model.LinearRegression()
X = war_df[X_cols]
y = war_df[y_col]
model = model.fit(X, y)
residuals = y - model.predict(X)
war_df['WAR_raw'] = residuals
print(war_df[['District', 'WAR_raw']].sort_values('WAR_raw').head(5))
war_df['WAR'] = war_df['WAR_raw'].map(lambda x: f'R +{round(x * 100, 1)}' if x > 0 else f'D +{round(-x * 100, 1)}')
full_data_df = full_data_df.merge(war_df[['District', 'WAR', 'WAR_raw']], how='left', left_on='District', right_on='District')

# merge with names
full_data_df = full_data_df.merge(names, how='inner')
full_data_df.to_csv('WAR Model 2022.csv', header=True)