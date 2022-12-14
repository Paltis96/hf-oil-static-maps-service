import logging
import os
from io import BytesIO
import sqlite3
import json

from shapely.geometry import mapping
from shapely import wkb
from colour import Color

import azure.functions as func

from .staticmap import StaticMap, Polygon, TextMarker, Line


PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = '/zcta.sqlite'

BASEMAPS = {'World_Street_Map': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Transportation': 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}',
            'World_Topo_Map': 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Reference_Overlay': 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Reference_Overlay/MapServer/tile/{z}/{y}/{x}',
            'NatGeo_World_Map': 'http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'}


def fetch_data(zip_list: list) -> list:
    geojson_list = list()

    con = sqlite3.connect(
        PATH + DB_PATH)

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
    if len(polygons) == 0:
        raise Exception("zips not found")

    img_io = BytesIO()
    m = StaticMap(width, height, 10, 10,
                  BASEMAPS['World_Topo_Map'])

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

# http://localhost:7071/api/static-maps?zips=11703,11704,11705,11706&height=1280&width=720


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    zip_list = list()

    zips = req.params.get('zips')
    width = req.params.get('width')
    height = req.params.get('height')

    if not width:
        width = 800
    if not height:
        height = 600

    try:
        zip_list = [int(x) for x in zips.split(',')]
        width = int(width)
        height = int(height)
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({'detail': str(e)}),
            status_code=422, mimetype="application/json")

    if len(zip_list) != 0:
        try:
            img = render_map(fetch_data(zip_list), height, width)
            return func.HttpResponse(body=img, mimetype="image/png")
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({'detail': "zips not found"}),
                status_code=404, mimetype="application/json",
            )

    else:
        return func.HttpResponse(
            body=json.dumps({'detail': "zip list is empty"}),
            status_code=404, mimetype="application/json",

        )
