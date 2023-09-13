import csv
import pandas as pd

import os
import glob


# Load the CSV file into a DataFrame
df= pd.read_csv('alt_names.csv')


countries = ["Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
            "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "The Bahamas", 
            "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin",
            "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", 
            "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", 
            "Cape Verde", "Central African Republic", 'Chad', "Chile", 
            "People's Republic of China", "Colombia", "Côte d'Ivoire",
              "Comoros", "Congo", "Democratic Republic of Congo", 
            "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic", "Denmark", 
            "Djibouti", "Dominica", "Eswatini",
            "Dominican Republic", "East Timor", "Ecuador", "Egypt", "El Salvador", 
            "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland",
            "France", "Gabon", "The Gambia", "Georgia", "Germany", "Ghana", "Greece", 
            "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", 
            "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", 
            "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", 
            "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea", "Kosovo", 
            "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", 
            "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "North Macedonia",
            "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", 
            "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia",
            "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
            "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand",
            "Nicaragua", "Niger", "Nigeria", "Norway", "Oman", "Pakistan", "Palestine",
            "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru",
            "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia",
            "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
            "Samoa", "San Marino", "São Tomé and Príncipe", "Saudi Arabia", "Senegal",
            "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
            "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain",
            "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", 
            "Syria","Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga", 
            "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
            "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", 
            "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
            "Zambia", "Zimbabwe"]


# Filter the DataFrame to keep only rows where the column matches items in the list
filtered_df = df[df["Country"].isin(countries)]

##To see if all images are there

# Specify the folder path where your PNG files are located
folder_path = '/images_noaxis'

# Use glob to find all PNG files in the folder
png_files = glob.glob(os.path.join(folder_path, '*.png'))

# Extract and print the file names without the .png extension
file_names = [os.path.basename(file).split('.')[0] for file in png_files]
# print([entry for entry in countries if entry not in file_names])
# print([entry for entry in file_names if entry not in countries])



path_image = ('https://github.com/amrutha-b-nair/Country_shape_quiz/tree/main/images_noaxis/' + filtered_df["Country"] + '.png').tolist()
filtered_df.loc[:,'Image_path'] = path_image

# print([country for country in df["Country"].tolist() if country not in countries ])
# print([entry for entry in countries if entry not in df['Country'].tolist()]
# )

# Specify the path where the filtered CSV file will be saved
filtered_csv = 'selected_names.csv'

# Save the filtered DataFrame as a new CSV file
filtered_df.to_csv(filtered_csv, index=False)


print((filtered_df['Other names']).tolist()[0])


