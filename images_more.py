import geopandas as gpd
import matplotlib.pyplot as plt
import os

# Load the GeoJSON file using geopandas
geojson_file = "/home/allu/quiz/geojson files/vatican.json"
gdf = gpd.read_file(geojson_file)

fig, ax = plt.subplots(figsize=(10, 10))
ax.axis('off')
# # # Plot the individual feature
gdf.plot(ax=ax, cmap="ocean")
# country.boundary.plot(ax=ax, linewidth=2, color='black')

country_name = gdf["name_engli"][0]
# # Optionally, you can customize the plot further, such as adding titles or labels.

# Save the plot as an image file (e.g., PNG)
output_image = f"/home/allu/quiz/images_noaxis/{country_name}.png"
plt.savefig(output_image, dpi=300, bbox_inches="tight")

# Close the plot to free up memory
plt.close()
