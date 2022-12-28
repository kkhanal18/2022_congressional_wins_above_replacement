import requests
import pandas as pd
from bs4 import BeautifulSoup

district_data = pd.read_csv('names.csv').fillna('No Candidate')
district_data['district_url_key'] = district_data['District'].map(lambda x: x.replace('-AL', '-01').replace('-', ''))
district_data['dem_lastname'] = district_data['Democrat'].map(lambda x: x.split(' ')[1])
district_data['rep_lastname'] = district_data['Republican'].map(lambda x: x.split(' ')[1])
url_prefix = 'https://www.opensecrets.org/races/outside-spending?cycle=2022&id='

def scrape_district_outside_spending(district_url_key, dem_lastname, rep_lastname):
	# the 4 things we want to get per district
	district_spending = {'dem_supported': 0, 'dem_opposed': 0, 'gop_supported': 0, 'gop_opposed': 0}
	opensecrets_url = url_prefix + district_url_key

	# the raw html data from the webpage
	html_text = requests.get(opensecrets_url).text
	soup = BeautifulSoup(html_text, 'lxml')
	table1 = soup.find('table', id='')
	if not table1:
		return district_spending
	headers = []
	for i in table1.find_all('th'):
		title = i.text
		headers.append(title)


	for j in table1.find_all('tr')[1:]:
		row_data = j.find_all('td')
		row = [i.text for i in row_data]
		# each row should have 4 entries in opensecrets: name, $ for, $ against, and total $ spent (for/against), in that order
		# if it has less than 4, skip the row!
		if len(row) < 4:
			continue
		row[0] = row[0].strip('\n\t')
		row[1] = float(row[1].strip('$').replace(',', ''))
		row[2] = float(row[2].strip('$').replace(',', ''))
		name, supported_spending, opposed_spending, _ = row
		if '(D)' in row[0] and row[0].split(',')[0] == dem_lastname:
			district_spending['dem_supported'] = supported_spending
			district_spending['dem_opposed'] = opposed_spending
		elif '(R)' in row[0] and row[0].split(',')[0] == rep_lastname:
			district_spending['gop_supported'] = supported_spending
			district_spending['gop_opposed'] = opposed_spending
		else:
			continue
	return pd.Series(district_spending)

district_data[['dem_supported', 'dem_opposed', 'gop_supported', 'gop_opposed']] = district_data.apply(lambda row: scrape_district_outside_spending(row['district_url_key'], row['dem_lastname'], row['rep_lastname']), axis=1)
district_data[['District', 'dem_supported', 'dem_opposed', 'gop_supported', 'gop_opposed']].to_csv('outside_spending.csv', sep=',', header=True)
print(district_data.head(5))
