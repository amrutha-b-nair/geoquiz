from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

wiki_url = "https://en.wikipedia.org/wiki/List_of_alternative_country_names"


response = requests.get(wiki_url)
response_text = response.text
soup = BeautifulSoup(response_text,'html.parser')

##remove all super scripts
for sup in soup.select('sup'):
    sup.extract()

table_soup = soup.find_all("table")

table_df = []
for table in table_soup:
    df = pd.read_html(str(table))[0]
    table_df.append(df)
 

tables_df = pd.concat(table_df, ignore_index=True)
tables_df = tables_df.rename(columns={'Other name(s) or older name(s)': 'Other names', "Description": "Country"})

#remove NaN
tables_df = tables_df[tables_df["Country"].notna()]
tables_df = tables_df.dropna(axis = 1, how = 'all')

tables_df["Country"] = tables_df["Country"].str.split(pat='(', n=1).str.get(0).str.strip().str.strip()
# tables_df["Other names"] = tables_df["Other names"].str.replace(r'\([^)]*\)', '', regex=True)


bold_elements = soup.find_all(['b', 'strong'])

# Extract and print the text from the bold elements
bold = []
for element in bold_elements:
    bold_text = element.get_text(strip=True)
    l1 = set(bold_text.split(' '))
    bold += l1


def filter_and_join_words(text, word_list):
    fragments = text.split(',')  # Split by commas
    filtered_fragments = []
    
    for fragment in fragments:
        words = fragment.split()  # Split by space
        filtered_words = [word for word in words if word in word_list]
        filtered_fragments.append(' '.join(filtered_words))  # Join with space
        
    return ', '.join(filtered_fragments)

# def remove_extra_commas(text):
#     return re.sub(r',+', ',', text)


# Apply the function to the DataFrame to filter and join words
tables_df['Other names'] = tables_df['Other names'].apply(filter_and_join_words, word_list=bold)
# tables_df['Other names'] = tables_df['Other names'].apply(remove_extra_commas)


# def remove_repeating_phrases(text):
#     # Split the text by commas
#     phrases = text.split(', ')

#     # Initialize a list to store unique phrases
#     unique_phrases = []

#     # Iterate through the phrases and add them to the list if they are not already present
#     for phrase in phrases:
#         if phrase not in unique_phrases:
#             unique_phrases.append(phrase)

#     # Join the unique phrases with commas to reconstruct the cleaned text
#     cleaned_text = ', '.join(unique_phrases)

#     return cleaned_text

# # Apply the function to the DataFrame to remove repeating phrases
# tables_df['Other names'] = tables_df['Other names'].apply(remove_repeating_phrases)

# # Print the DataFrame with cleaned text




tables_df['Other names'].apply(filter_and_join_words, word_list=bold)

def remove_non_latin(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

# Apply the function to the column to remove non-Latin script characters
tables_df["Other names"] = tables_df["Other names"].apply(remove_non_latin)

tables_df.loc[tables_df['Country'] == 'Republic of China', 'Country'] = 'Taiwan'

print((tables_df['Other names']).tolist()[1])

tables_df["Other names"] = tables_df['Country'] +',' +tables_df["Other names"]

print((tables_df['Other names']).tolist()[1])

fname = "alt_names.csv"
tables_df.to_csv(fname, index=False)   

df1 = pd.read_csv('alt_names.csv')

# Display the first five rows of the DataFrame
# print(df1)

# print(list(df1["Other names"]))

# print(list(df1["Country"]))

