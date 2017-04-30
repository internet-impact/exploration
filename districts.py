import geopandas as gpd
import pandas as pd
import seaborn as sns
import numpy as np
import folium
import matplotlib.pyplot as plt

from shapely.ops import unary_union, cascaded_union

def get_all_shapes(path):
    dirs = [f[0] for f in os.walk(path)]
    return [gpd.GeoDataFrame.from_file(f) for f in dirs[1:]]

def get_poly(gdf, i):
    return gdf.geometry.iloc[i]

def get_by_id(src, target):
    return src[src['VDNumber'] == int(target['VDNumber'])]

districts = get_all_shapes('../voting/shapefiles/districts')

municipalities = get_all_shapes('../voting/shapefiles/municipalities')

# get number in A
a = districts[0][0:1]
# intersect with b
districts[0][0:1].intersects(districts[1])

get_poly(get_by_id(districts[0], districts[1][7:8]))


# intersects, minus intersections where area < some threshold.

def get_intersections(df, poly, thresh = 0.1):
    t = poly.area * thresh
    inters = df[df.intersects(poly)]
    return inters[inters.intersection(poly).area > t]

def resolve(first, second, i):
    p = get_poly(first, i)

def filter_prov(df, prov):
    return df[df.PROVINCE == prov]

def count_all_intersections(before, after, prov):
    before, after = filter_prov(before, prov), filter_prov(after, prov)
    intersections = [get_intersections(after, get_poly(before, i)).assign(before = before.VDNumber.iloc[i])
                     for i in range(0, before.shape[0] - 1)]
    return[i for i in intersections if i.shape[0] > 1]

# given previous ID(s) and curr IDs, it finds intersections, dissolves, and returns combined ids


def d2(group):
    agg = lambda a: reduce(lambda b,c: np.unique(np.append(b,c)), a)
    return { 'curr': agg(group.curr),
             'prev': agg(group.prev),
             'geometry': cascaded_union(group.geometry)}

def dissolver(group):
    return { 'curr': group.VDNumber.values,
             'prev': group.before.unique(),
             'geometry': cascaded_union(group.geometry)}

def cross_dissolver(df):
    intersections = [get_intersections(df, get_poly(df, i)) for i in range(df.shape[0] - 1)]
    return [i for i in intersections if i.shape[0] > 1]


cs = cross_dissolver(gpd.GeoDataFrame(map(dissolver, groups)))
df = gpd.GeoDataFrame(map(d2, cs))

# remove the curr and prev from o.g. DF
# combine this df to curr and prev DF
# which one to use??? they should be the same from a geometric perspective
# then move on...





# gpd.GeoDataFrame(map(dissolver, groups[0:10]))


# def countem():
#     provinces = before.PROVINCE.unique()
#     [count_all_intersections(before, after, p) for p in provinces]
