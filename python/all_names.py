import pandas as pd

def wiki_to_csv(wikiurl = str):
    link = wikiurl
    tables = pd.read_html(link, header=0)
    print(tables[1]["Description"])

    combined_table = pd.concat(tables, ignore_index=True)
    combined_table["Description"] = combined_table["Description"].str.strip()
    columns_to_remove = [combined_table.columns[0], combined_table.columns[1]]

    new_table = combined_table.drop(columns = columns_to_remove)
    
    new_table["Description"] = new_table["Description"].str.split('(', 1).str.get(0)
    # print(list(new_table["Description"]))

    # fname = "alt_names.csv"
    # new_table.to_csv(fname, index=False)


wiki_to_csv("https://en.wikipedia.org/wiki/List_of_alternative_country_names")