import geopandas as gpd
import pandas as pd
import numpy as np
import os
from shapely.ops import unary_union, cascaded_union
import re

def get_poly(gdf, i):
    return gdf.geometry.iloc[i]

def get_by_id(src, target):
    return src[src['vdnumber'] == int(target['vdnumber'])]

def filter_prov(df, prov):
    return df[df.province.str.lower() == prov.lower()]

def get_years(df):
    return [c for c in df.columns if c != 'geometry']

def has_prev(df, i):
    curr = sorted(get_years(df))[0]
    return len(df[curr].iloc[i]) > 0

def lowercase_cols(df):
    return df.rename(columns = lambda s: s.lower())

def get_intersections(df, poly, thresh = 0.1):
    buffit = lambda p: p.buffer(0)
    try:
        inters = df[df.intersects(poly)]
        print inters.shape[0]
        intersections = inters.intersection(poly)
    except:
        print '**'
        df.geometry = df.geometry.map(buffit)
        poly = buffit(poly)
        inters = df[df.intersects(poly)]
        print inters.shape[0]
        intersections = inters.intersection(poly)

    # We check that the intersection is not too far from one or
    # the other, otherwise it's probably a mistake in recording.
    return inters[(intersections.area > poly.area*thresh) |
                  (intersections.area > inters.area*thresh)]

def make_empty_ids(length):
    return [np.array([]) for i in range(length)]

def reformat(df, years): # take year and make that the column
    year = df.year.unique()[0]
    from_number = df.vdnumber.map(lambda v: np.array([v]))
    empty = make_empty_ids(df.shape[0])
    df = gpd.GeoDataFrame({ 'geometry': df.geometry })
    df = reduce(lambda d,y: d.assign(**{ y: empty }), years, df)
    return df.assign(**{ year: from_number })

def formatted_df(before, after, years = ['2006', '2011', '2016']):
    years = [before.year.iloc[0], after.year.iloc[0]]
    before, after = reformat(before, years), reformat(after, years)
    return gpd.GeoDataFrame(pd.concat([before, after]))

def get_union(series):
    try:
        return cascaded_union(series)
    except ValueError:
        print '*'
        s = series.map(lambda p: p.buffer(0))
        return cascaded_union(s)


def dissolver(group):
    agg = lambda a: reduce(lambda b,c: np.unique(np.append(b,c)), a)
    base = {'geometry': get_union(group.geometry)}
    [base.update({col: agg(group[col])})
     for col in group.columns if col != 'geometry']
    return base

def dissolve(groups):
    return gpd.GeoDataFrame(map(dissolver, groups))

def cross_dissolver(df, thresh):
    intersections = [get_intersections(df, get_poly(df, i), thresh)
                     for i in range(df.shape[0])

                     # optmization to not double-up on first round
                     if has_prev(df, i)]

    # If the only intersection is itself, we consider this stable
    stable = [i for i in intersections if i.shape[0] == 1]
    changing = [i for i in intersections if i.shape[0] > 1]
    return dissolve(stable), dissolve(changing)

def one_round(to_merge, thresh, stable = gpd.GeoDataFrame([])):
    new_stable, to_fix = cross_dissolver(to_merge, thresh)
    stable = pd.concat([stable, new_stable])
    # to_fix = to_fix[[len(c) > 1 for c in to_fix.curr]]
    return remove_duplicates(to_fix), stable

def recursively_dissolve(to_merge, thresh, stable = None):
    to_merge, stable = one_round(to_merge, thresh, stable)

    # Base cae is when we run out of rows in our dataframe to merge
    if to_merge.shape[0] > 0:
        print 'recursing'
        print to_merge.shape[0], stable.shape[0]
        return recursively_dissolve(to_merge, thresh, stable)
    else:
        return stable



def format_for(df, fn):
    years = get_years(df)
    new_df = gpd.GeoDataFrame({ 'geometry': df.geometry })
    return reduce(lambda d,y: d.assign(**{ y: df[y].map(fn) }), years, new_df)

def join_array(arr):
    return ','.join(map(str, map(int, arr)))

def format_for_printing(df):
    return format_for(df, join_array)

def make_array(s):
    return np.array(map(int, s.split(',')))

def format_for_working(df):
    return format_for(df, make_array)

def remove_duplicates(df):
    if df.shape[0] == 0:
        return df
    return format_for_working(format_for_printing(df)
                              .drop_duplicates(get_years(df)))

def get_year_from_path(path):
    return re.findall('.+\/(.+)$', path)[0]

def get_file_with_year(path):
    y = get_year_from_path(path)
    return gpd.GeoDataFrame.from_file(path).assign(year = y)

def get_all_shapes(path):
    dirs = [f[0] for f in os.walk(path)][1:]
    return [get_file_with_year(f) for f in dirs]

def combining(dfs, thresh):
    dfs = map(lowercase_cols, dfs)
    years = [d.year.iloc[0] for d in dfs]
    dfs = [reformat(d, years) for d in dfs]
    df = gpd.GeoDataFrame(pd.concat(dfs))
    return recursively_dissolve(df, thresh)

def all_districts(dfs, thresh):
    dfs = map(lowercase_cols, dfs)
    provinces = dfs[0].province.unique()
    filtered_dfs_lists = [[filter_prov(df, prov) for df in dfs] for prov in provinces]
    combined = [combining(dfs, thresh) for dfs in filtered_dfs_lists]
    return pd.concat(combined)

##############################################
# CLI
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--path', '-p')
args = vars(parser.parse_args())

districts = get_all_shapes(args['path'])
districts = [d for d in districts if d.year.iloc[0] in ['2000', '2006']]
output = all_districts(districts, 0.05)
format_for_printing(output).to_file('output')


# ###############################################
# # interactive
# districts = get_all_shapes('../voting/shapefiles/districts')
# districts = [d for d in districts if d.year.iloc[0] != '2000']
# filtered = [filter_prov(d, 'limpopo') for d in districts]
# format_for_printing(combining(filtered, 0.05)).to_file('limpopo')

# ###############################################
# Nationals
# districts = get_all_shapes('./nationals')
# format_for_printing(all_districts(districts, 0.05)).to_file('national_out')
