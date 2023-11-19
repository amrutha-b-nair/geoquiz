from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import numpy as np

wiki_url_gdp = "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)"
wiki_url_area = "https://en.wikipedia.org/wiki/List_of_countries_and_dependencies_by_area"


response_gdp = requests.get(wiki_url_gdp)
response_text_gdp = response_gdp.text
soup_gdp = BeautifulSoup(response_text_gdp,'html.parser')

#remove all super scripts
for sup in soup_gdp.select('sup'):
    sup.extract()

table_soup_gdp = soup_gdp.find_all("table")

table_gdp = [table for table in table_soup_gdp if table.caption is not None]

table_df_gdp = pd.read_html(str(table_gdp))[0]
columns_gdp = table_df_gdp.columns
table_df_gdp = table_df_gdp[[columns_gdp[0],columns_gdp[2], columns_gdp[-2]]]
table_df_gdp.columns = table_df_gdp.columns.droplevel()
columns_gdp = table_df_gdp.columns
table_df_gdp.rename(columns={columns_gdp[0]:'Country'}, inplace=True)
table_df_gdp.rename(columns={columns_gdp[-1]:'GDP'}, inplace=True)

table_df_gdp['GDP'].replace('—', np.nan, inplace=True)
table_df_gdp['GDP'].fillna(table_df_gdp[columns_gdp[1]], inplace=True)




response_area = requests.get(wiki_url_area)
response_text_area = response_area.text
soup_area = BeautifulSoup(response_text_area,'html.parser')

#remove all super scripts
for sup in soup_area.select('sup'):
    sup.extract()

table_soup_area = soup_area.find_all("table")

table_area = table_soup_area[1]

table_df_area = pd.read_html(str(table_area))[0]
columns_area = table_df_area.columns


table_df_area = table_df_area[[columns_area[1], columns_area[2]]]
columns_area = table_df_area.columns

table_df_area[columns_area[1]] = table_df_area[columns_area[1]].str.split(pat='(', n=1).str.get(0).str.strip()

table_df_area.rename(columns={columns_area[0]:'Country'}, inplace=True)

table_df_area.rename(columns={columns_area[1]:'Area'}, inplace=True)
table_df_area.columns = table_df_area.columns.str.strip()


merged_df = pd.merge(table_df_gdp, table_df_area, on='Country', how='inner')

merged_df['Area'] = merged_df['Area'].str.replace(',', '').astype(float)
merged_df['GDP'] = merged_df['GDP'].str.replace(',', '').astype(float)

# print(merged_df['Area'].tolist())
# print(merged_df['GDP'].tolist())

merged_df['Value'] = ((merged_df['Area'])*merged_df['GDP'])*10**(-9)
df_sorted = merged_df.sort_values(by='Value', ascending=False)

df_sorted.loc[df_sorted['Country'] == 'Ivory Coast', 'Country'] = "Côte d'Ivoire"
df_sorted.loc[df_sorted['Country'] == 'Gambia', 'Country'] = "The Gambia"
df_sorted.loc[df_sorted['Country'] == 'Bahamas', 'Country'] = "The Bahamas"
df_sorted.loc[df_sorted['Country'] == 'DR Congo', 'Country'] = "Democratic Republic of Congo"
df_sorted.loc[df_sorted['Country'] == 'China', 'Country'] = "People's Republic of China"

fname = "gdp_area.csv"
df_sorted.to_csv(fname, index=False)   

# df1 = pd.read_csv('gdp_area.csv')
