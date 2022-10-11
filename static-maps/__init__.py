from array import array
import logging
from .staticmap import StaticMap, Polygon, TextMarker, Line

from io import BytesIO
import sqlite3
from shapely.geometry import mapping
from shapely import wkb
import os
import azure.functions as func
from colour import Color

PATH = f'{os.path.dirname(os.path.abspath(__file__))}/'
DB_NAME = 'zcta.sqlite'

BASEMAPS = {'World_Street_Map': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Transportation': 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
            'World_Topo_Map': 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Reference_Overlay': 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer/tile/{z}/{y}/{x}',
            'NatGeo_World_Map': 'http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'}


def fetch_data(zip_list: array) -> list:
    geojson_list = list()

    con = sqlite3.connect(
        PATH + DB_NAME)

    cur = con.cursor()
    res = cur.execute(
        "SELECT GEOMETRY FROM zcta WHERE geoid10 IN (%s)" % ', '.join([str(elem) for elem in zip_list]))
    for row in res.fetchall():
        row_geom = wkb.loads(row[0])
        if row_geom.geom_type == 'MultiPolygon':
            geojson_list = geojson_list + [geom for geom in row_geom]
        else:
            geojson_list.append(row_geom)

    return geojson_list


def render_map(polygons: list, width: int, height: int):

    img_io = BytesIO()
    m = StaticMap(width, height, 10, 10,
                  BASEMAPS['World_Topo_Map'])

    if len(polygons) == 0:
        return func.HttpResponse(
            "Zips not found",
            status_code=404
        )
    color_base = Color("#FDBB2D")
    colors = list(color_base.range_to(Color("#22C1C3"), len(polygons)))
    for idx, coords in enumerate(polygons):
        coord_list = mapping(coords)['coordinates'][0]
        m.add_polygon(
            Polygon(coord_list, f'{colors[idx].hex_l}80', colors[idx].hex_l, False))
        m.add_line(Line(coord_list, colors[idx].hex_l, 2, False))
        
        # centroid_list = mapping(coords.centroid)['coordinates']
        # m.add_marker(TextMarker(list(centroid_list), '#0E8BDE' , 'long test text',18))

    image = m.render()

    image.save(img_io, format='png')
    img_io.seek(0)
    return img_io.read()


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    headers = {"media-type": "image/png"}

    zips = req.params.get('zips')
    width = int(req.params.get('width'))
    height = int(req.params.get('height'))

    if not width:
        width = 800
    if not height:
        height = 600

    zip_list = [int(x) for x in zips.split(',')]

    img = render_map(fetch_data(zip_list), height, width)
    if zips:
        return func.HttpResponse(body=img, headers=headers)
    else:
        return func.HttpResponse(
            "Zips not found",
            status_code=404
        )
