import numpy as np
import pandas as pd
from sklearn import linear_model

war_df = pd.read_csv('WAR Model 2022 SKINNY.csv', header=0)
#######################################
# PLOT WHAT'S HAPPENING
map_df = gpd.read_file("congress_shapefile/2020s Adopted CDs USA.shp")
map_df['CDNAME'] = map_df['CDNAME'].apply(lambda x: x.split('-')[0] + '-' + x.split('-')[1].zfill(2))

map_df = map_df.to_crs(epsg=2163)
# print(sorted(map_df['STATEFP'].unique()))
# JOIN + TRANSFORM
map_df = map_df.merge(war_df[['District', 'WAR_raw']], left_on="CDNAME", right_on="District", how="left")

map_df['WAR_raw'] = map_df['WAR_raw'] * -100

map_df = map_df[~map_df['District'].isin(['AK-AL', 'HI-01', 'HI-02'])]
# BUCKET THE MARGINS
map_df['performance_bucket'] = 4.0
map_df.loc[map_df['WAR_raw'] > -90, 'performance_bucket'] = 0
map_df.loc[map_df['WAR_raw'] > -10, 'performance_bucket'] = 1
map_df.loc[map_df['WAR_raw'] > -5, 'performance_bucket'] = 2
map_df.loc[map_df['WAR_raw'] > -2.5, 'performance_bucket'] = 3
map_df.loc[map_df['WAR_raw'] == 0, 'performance_bucket'] = 4
map_df.loc[map_df['WAR_raw'] > 0, 'performance_bucket'] = 5
map_df.loc[map_df['WAR_raw'] > 2.5, 'performance_bucket'] = 6
map_df.loc[map_df['WAR_raw'] > 5, 'performance_bucket'] = 7
map_df.loc[map_df['WAR_raw'] > 10, 'performance_bucket'] = 8

for i in range(9):
    map_df.loc['dummy_' + str(i), 'performance_bucket'] = float(i)

# PLOT
f, ax = plt.subplots(1, figsize=(12, 9))

cmap = plt.cm.get_cmap("RdBu", 9)
ax = map_df.plot(column="performance_bucket", cmap=cmap, edgecolor="black", linewidth=0.25, ax=ax)
ax.legend([mpatches.Patch(color=cmap(b)) for b in list(range(9))],
           ['> R +10', 'R +5 - R +10', 'R +2.5 - R +5', 'R +2.5 - EVEN', 'UNCONTESTED', 'EVEN - D +2.5', 'D +2.5 - D +5', 'D +5 - D +10', 'D > +10'], loc=(.90, .18), title="Performance vs expectations")

ax.set_axis_off()

plt.gca().set_axis_off()
plt.subplots_adjust(top = 0.95, bottom = 0.05, right = 0.95, left = 0.05, 
            hspace = 0.05, wspace = 0.05)
plt.margins(0,0)
plt.gca().xaxis.set_major_locator(plt.NullLocator())
plt.gca().yaxis.set_major_locator(plt.NullLocator())

plt.title("2022 House Elections —– Wins Above Replacement", fontsize=18)
plt.figtext(0.55, 0.11, '@SplitTicket_, @LXEagle17, @HWLavelleMaps, @Thorongil16', horizontalalignment='left')
plt.figtext(0.55, 0.08, 'Sources: Census Bureau, DKE, Split Ticket, @cinyc9, @maxtmcc', horizontalalignment='left')
plt.show()
