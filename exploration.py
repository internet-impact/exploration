# folium?? Nice to bring in open street maps via http api

# import folium


# folium.GeoJson(open('../MESO/geojson/meso_2010_econ_dd.geojson'),
#                name='econ'
#               ).add_to(map_osm)

# map_osm.save('osm.html')





import geopandas as gpd
import pandas as pd
import statsmodels
import seaborn as sns
import numpy as np
import folium

mobile_df = gpd.GeoDataFrame.from_file('../data/2009/Data/3G')
mobile_df['geometry'] = mobile_df.buffer(0)

econ_df = gpd.GeoDataFrame.from_file('../MESO/meso_2010_econ_dd').to_crs(epsg=4326)


populist = econ_df.sort_values(['POP07'], ascending=False)[0:20]
inter = gpd.overlay(populist, mobile_df, how = 'intersection')

mid_populist = econ_df.sort_values(['POP07'], ascending=False)[20:60]
mid_inter = gpd.overlay(mid_populist, mobile_df, how = 'intersection')

low_populist = econ_df.sort_values(['POP07'], ascending=False)[60:200]
low_inter = gpd.overlay(low_populist, mobile_df, how = 'intersection')

def compare_areas(x,y):
    return sum(x.area)/sum(y.area)


def add_covered(base, inter, id_key = 'MESO_ID'):
    base = base.copy()
    base['covered_area'] = [sum(inter[inter[id_key] == i].area) for i in base[id_key]]
    base['covered_percentage'] = base['covered_area']/base.area
    return base

def intersect(base, mobile):
    inter = gpd.overlay(base, mobile, how = 'intersection')
    return add_covered(base, inter)


inter = intersect(econ_df.sort_values('POP07', ascending=False)[0:300], mobile_df)
inter['density'] = inter['POP07']/inter['AREA_TOT']


map_js = folium.Map(location=[-33.2949, 18.4241], tiles = 'Stamen Terrain')
inter_json = inter[['geometry', 'MESO_ID']].to_json()

not_covered = inter[inter['covered_percentage'] < 0.3 ].to_json()

map_js.choropleth(geo_str = not_covered, data = inter, columns=['MESO_ID', 'density'], key_on='feature.properties.MESO_ID', fill_color='BuGn')
map_js.save('econ.html')
