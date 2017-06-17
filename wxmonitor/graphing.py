from mpl_toolkits.basemap import Basemap



_default_state_boundry_options = dict(linewidth=0.5, linestyle="solid", color=(0,0,0),
                                      antialiased=1, ax=None, zorder=None)

_default_county_boundry_options = dict(linewidth=0.1, linestyle="solid", color=(0,0,0),
                                       antialiased=1, ax=None, zorder=None, drawbounds=False)


def make_basemap(lat_0, lon_0, lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat):
    m = Basemap(projection='lcc', lat_0=lat_0, lon_0=lon_0,
                resolution='h', area_thresh=0.1,
                llcrnrlon=lower_left_lon, llcrnrlat=lower_left_lat,
                urcrnrlon=upper_right_lon, urcrnrlat=upper_right_lat)

    m.drawcoastlines()
    m.drawcountries()
    m.drawstates(**_default_state_boundry_options)
    m.drawcounties(**_default_county_boundry_options)
    m.drawmapboundary()

    # monkey patch on the county poly map.
    m.county_poly_map = {}
    for i, county in enumerate(m.counties_info):
        county_hash = make_county_hash(county["STATE"], county["NAME"])
        m.county_poly_map[county_hash] = m.counties[i]

    return m


def get_rgb(val, min, max):
    mid = min + (max - min) / 2

    if val > mid:
        perc_left = (max - val) / (max - mid)
        b = 0
        g = 1.0 * perc_left
        r = 1.0 * (1 - perc_left)

    elif val < mid:
        perc_left = (mid - val) / (mid - min)
        b = 1.0 * perc_left
        g = 1.0 * (1 - perc_left)
        r = 0

    else:
        r = 0
        g = 1
        b = 0

    return [r, g, b]


def make_county_hash(state, county):
    if type(state) == str:
        state = bytes(state, "UTF8")
    if type(county) == str:
        county = bytes(county, "UTF8")
    return (state + b"_" + county).lower()