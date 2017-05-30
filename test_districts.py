from shapely.geometry import Polygon
import geopandas as gpd
import pandas as pd
import numpy as np
from districts import get_intersections, formatted_df, one_round, recursively_dissolve, cross_dissolver, dissolve, reformat, combining, has_prev

a = [(0,0), (2,0), (2,2), (0,2)]
b = [(2,0), (4,0), (4,2), (2,2)]
c = [(0,2), (2,2), (2,1), (0,0)]

d = [(0,0), (4,0), (4,2), (0,2)]

x = [(0,0), (1,0), (1,2), (0,2)]
y = [(1,0), (3,0), (3,2), (1,2)]
z = [(3,0), (4,0), (4,2), (3,2)]
zz = [(0,2), (4,2), (4,4), (0,4)]


year_a = gpd.GeoDataFrame({
    'geometry': [Polygon(a), Polygon(b)],
    'vdnumber': [1, 2],
    'year': ['2006', '2006']
})

year_b = gpd.GeoDataFrame({
    'geometry': [Polygon(x), Polygon(y), Polygon(z)],
    'vdnumber': [3, 4, 5],
    'year': ['2011', '2011', '2011']
})


big = [(0,0), (1.9, 0), (1.9, 2), (0,2)]
med = [(1.9, 0), (2,0), (2,1.9), (1.9, 1.9)]
small = [(1.9, 1.9), (2, 1.9), (2, 2), (1.9, 2)]

with_children = gpd.GeoDataFrame({
    'geometry': [Polygon(big), Polygon(med), Polygon(small)],
    'vdnumber': [1,2,3],
    'year': ['2006', '2006', '2006'],
})


def test_get_intersections_ignores_neighbors():
    inters = get_intersections(year_a, Polygon(a))
    assert inters.shape[0] == 1

def test_get_intersections_ignores_threshold_overlap():
    b_close = [(1.9, 0), (4.01, 0), (4, 2), (2,2)]
    inters = get_intersections(year_a, Polygon(b_close))
    assert inters.shape[0] == 1

def test_get_intersections_can_detect_small_children():
    inters = get_intersections(with_children, Polygon(a))
    assert inters.shape[0] == 3

def test_has_prev():
    assert has_prev(reformat(year_a, years = ['2006', '2011']), 0) == True
    assert has_prev(reformat(year_a, years = ['2003', '2006']), 0) == False

def test_reformat():
    ref = reformat(year_a, ['2006','2011', '2016'])
    assert np.array_equal(ref.columns, ['geometry', '2006', '2011', '2016'])
    assert np.array_equal(ref['2016'].iloc[0], [])
    assert np.array_equal(ref['2006'].iloc[0], [1])
    assert np.array_equal(ref['2006'].iloc[1], [2])


group_1 = gpd.GeoDataFrame({'2006': [np.array([]), np.array([])],
                            '2011': [np.array([1]), np.array([2])],
                            'geometry': [Polygon(a), Polygon(b)]})

group_2 = gpd.GeoDataFrame({'2006': [np.array([]), np.array([]), np.array([])],
                            '2011': [np.array([3]), np.array([4]), np.array([4])],
                            'geometry': [Polygon(a), Polygon(b), Polygon(c)]})

group_3 = gpd.GeoDataFrame({'2006': [np.array([1]), np.array([])],
                            '2011': [np.array([]), np.array([1])],
                            'geometry': [Polygon(a), Polygon(a)]})

group_4 = gpd.GeoDataFrame({'2006': [np.array([1])],
                            '2011': [np.array([1])],
                            'geometry': [Polygon(a)]})

def test_dissolve():
    groups = [group_1, group_2]
    df = dissolve(groups)
    assert df.shape[0] == 2
    assert df.iloc[1].geometry.area == Polygon(d).area
    assert df.iloc[0].geometry.area == Polygon(d).area

    # flattens the correct columns together
    assert np.array_equal(df.iloc[0]['2011'], np.array([1,2]))
    assert np.array_equal(df.iloc[0]['2006'], np.array([]))

    # uniques the ids
    assert np.array_equal(df.iloc[1]['2011'], [3,4])

def test_dissolve_with_single_stable_group():
    df = dissolve([group_3])
    assert df.iloc[0].geometry.equals(Polygon(a))
    assert np.array_equal(df.iloc[0]['2011'], np.array([1]))
    assert np.array_equal(df.iloc[0]['2006'], np.array([1]))

def test_dissolve_doesnt_ruin_stable_rows():
    df = dissolve([group_4])
    assert df.shape == group_4.shape
    assert df.geometry.equals(group_4.geometry)
    assert df['2011'].equals(group_4['2011'])
    assert df['2006'].equals(group_4['2006'])


zza = [(0,2), (2,2), (2,4), (0,4)]
zzb = [(2,2), (4,2), (4,4), (2,4)]

xc = [(0,0), (1,0), (1,1.5), (0,1.5)]
yc = [(1,0), (3,0), (3,1.5), (1,1.5)]
zc = [(3,0), (4,0), (4,1.5), (3,1.5)]
zzc = [(0,1.5), (4,1.5), (4,4), (0,4)]

year_c = gpd.GeoDataFrame({
    'geometry': [Polygon(a), Polygon(b), Polygon(zz)],
    'vdnumber': [1, 2, 6],
    'year': ['2011', '2011', '2011']
})

year_d = gpd.GeoDataFrame({
    'geometry': [Polygon(x), Polygon(y), Polygon(z), Polygon(zz)],
    'vdnumber': [3, 4, 5, 6],
    'year': ['2016', '2016', '2016', '2016']
})

year_e = gpd.GeoDataFrame({
    'geometry': [Polygon(x), Polygon(y), Polygon(z), Polygon(zza), Polygon(zzb)],
    'vdnumber': [3, 4, 5, 6, 7],
    'year': ['2021', '2021', '2021', '2021', '2021']
})

year_f = gpd.GeoDataFrame({
    'geometry': [Polygon(xc), Polygon(yc), Polygon(zc), Polygon(zzc)],
    'VDNumber': [5,6,7,8], # test lowercasing
    'year': ['2026', '2026', '2026', '2026']
})

def test_cross_dissolving_never_returns_stable_on_first_round():
    df = formatted_df(year_a, year_b)
    stable, changing = cross_dissolver(df, 0.05)
    assert stable.shape[0] == 0
    assert changing.shape[0] == 2
    assert changing.iloc[0].geometry.area == 6
    assert changing.iloc[1].geometry.area == 6

def test_one_round_works_with_stable_side():
    df = formatted_df(year_c, year_d)
    changing, stable = one_round(df, 0.05)
    changing, stable = one_round(changing, 0.05)
    assert stable.shape[0] == 1
    assert changing.shape[0] == 1

def test_dissolving_dissolves_it_all():
    df = formatted_df(year_a, year_b)
    dissolved = recursively_dissolve(df, .1)
    assert dissolved.shape[0] == 1
    assert np.array_equal(dissolved['2006'].iloc[0], [1,2])
    assert np.array_equal(dissolved['2011'].iloc[0], [3,4,5])

def test_dissolving_leaves_stable_areas_untouched():
    df = formatted_df(year_c, year_d)
    dissolved = recursively_dissolve(df, .1)
    assert dissolved.shape[0] == 2
    assert dissolved['2016'].iloc[0] == [6]
    assert dissolved['2011'].iloc[0] == [6]
    assert np.array_equal(dissolved['2016'].iloc[1], [3,4,5])
    assert np.array_equal(dissolved['2011'].iloc[1], [1,2])

# def test_dissolving_works_with_empty_df():
#     df = formatted_df(year_d, year_d)
#     dissolved = recursively_dissolve(0.05)

def test_dissolving_works_with_same_df():
    # WHAT DO WE WANT????
    df = formatted_df(year_d, year_d)
    dissolved = recursively_dissolve(df, 0.05)
    assert dissolved.shape[0] == year_d.shape[0]
    assert dissolved.geometry.iloc[0].equals(year_d.geometry.iloc[0])
    assert dissolved.geometry.iloc[1].equals(year_d.geometry.iloc[1])
    assert dissolved['2016'].iloc[1][0] == year_d.vdnumber.iloc[1]
    assert dissolved['2016'].iloc[1][0] == year_d.vdnumber.iloc[1]

def test_dissolving_multiple_years():
    districts = [year_c, year_d, year_e]
    dissolved = combining(districts, 0.05)
    assert dissolved.shape[0] == 2
    assert np.array_equal(dissolved['2016'].iloc[0], [6])
    assert np.array_equal(dissolved['2021'].iloc[0], [6,7])
    assert np.array_equal(dissolved['2016'].iloc[1], [3,4,5])
    assert np.array_equal(dissolved['2011'].iloc[1], [1,2])

def test_dissolving_into_one_big_blob():
    districts = [year_c, year_d, year_e, year_f]
    dissolved = combining(districts, 0.05)
    assert dissolved.shape[0] == 1
    assert np.array_equal(dissolved['2016'].iloc[0], [3,4,5,6])
    assert np.array_equal(dissolved['2021'].iloc[0], [3,4,5,6,7])
    assert np.array_equal(dissolved['2026'].iloc[0], [5,6,7,8])


# def test_turnover_year():
#     df = gpd.GeoDataFrame({'curr': [np.array([1,2,3]), np.array([4,5])],
#                            'prev': [np.array([6,7]), np.array([8,9,10])],
#                            'geometry': [Polygon(a), Polygon(b)]})
#     old, new_df = turnover_year(df)
#     assert np.array_equal(new_df.curr.iloc[0], [])
#     assert np.array_equal(new_df.prev.iloc[0], df.curr.iloc[0])
#     assert np.array_equal(old.iloc[0], df.prev.iloc[0])
#     assert new_df.geometry.iloc[0].equals(df.geometry.iloc[0])
#     assert new_df.geometry.iloc[1].equals(df.geometry.iloc[1])
