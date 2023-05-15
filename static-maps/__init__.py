import logging
import os
from io import BytesIO
import json
import os
import sqlite3
from shapely.geometry import mapping, MultiPolygon
from shapely import wkb
from shapely.ops import unary_union

import azure.functions as func

from .staticmap import StaticMap, Polygon, TextMarker, Line


PATH = os.path.dirname(os.path.abspath(__file__))
DB_PATH = 'zcta.sqlite'

BASEMAPS = {'Waze': 'https://livemap-tiles3.waze.com/tiles/{z}/{x}/{y}.png',
            'Voyager': 'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png',
            'Positron': 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
            'ESRI_Standard': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Street_Map': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Topo_Map': 'https://services.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'World_Dark_Gray_Base':' http://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
            'World_Light_Gray_Base': 'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
            'World_Imagery':'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'World_Physical_Map':' https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
            'dark_all':'http://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
            'NatGeo_World_Map': 'http://services.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}'}


class DataConn:
    def __init__(self, db_path) -> None:
        self._db_path = db_path

    def __enter__(self):
        self.conn = sqlite3.connect(self._db_path)
        return self.conn

    def __exit__(self, *args):
        self.conn.close()


def fetch_data(zip_list: list, union) -> list:
    geo_id_list = list()
    with DataConn(os.path.join(PATH, DB_PATH)) as conn:
        cur = conn.cursor()
        res = cur.execute("""--sql
            SELECT GEOMETRY FROM zcta
            WHERE geoid20 IN (%s)
            """ % ', '.join([str(elem) for elem in zip_list]))
        for row in res.fetchall():
            row_geom = wkb.loads(row[0])
            if isinstance(row_geom, MultiPolygon):
                geo_id_list.extend(list(row_geom.geoms))
            else:
                geo_id_list.append(row_geom)
        logging.info(union)
        if union:
            geo_id_list = unary_union(geo_id_list)
            if isinstance(geo_id_list, MultiPolygon):
                geo_id_list = list(geo_id_list.geoms)

        return geo_id_list


def render_map(polygons: list, height: int, width: int, style, color):
    color = '#' + color
    img_io = BytesIO()
    m = StaticMap(width, height, 10, 10,
                  BASEMAPS[style])

    if isinstance(polygons, list):
        if len(polygons) == 0:
            raise Exception("zip not found")
        for coords in polygons:
            coord_list = mapping(coords)['coordinates'][0]
            m.add_polygon(
                Polygon(coord_list, color + '45', color, False))
            m.add_line(Line(coord_list, color, 1, False))

    else:
        coord_list = mapping(polygons)['coordinates'][0]
        m.add_polygon(
            Polygon(coord_list, color + '45', color, False))
        m.add_line(Line(coord_list, color, 1, False))

    # color_base = Color("#FDBB2D")
    # colors = list(color_base.range_to(Color("#22C1C3"), len(polygons)))

    # centroid_list = mapping(coords.centroid)['coordinates']
    # m.add_marker(TextMarker(list(centroid_list), '#0E8BDE' , 'long test text',18))

    image = m.render()
    image.save(img_io, format='WebP')
    img_io.seek(0)
    return img_io.read()

# http://localhost:7071/api/static-maps?color=0E8BDE&union=1&style=Voyager&zip=67002,67010,67013,67016,67017,67020,67026,67030,67031,67212,67213,67216,67228,67230,67232,67211,67214,67215,67217,67218,67219,67220,67223,67226,67227,67235,67260,67001,67037,67039,67042,67050,67052,67055,67056,67060,67067,67101,67108,67110,67114,67120,67123,67133,67135,67144,67146,67147,67149,67152,67154,67202,67203,67204,67205,67206,67207,67208,67209,67210&height=720&width=1280


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    zip_list = list()

    color = req.params.get('color')
    if not color:
        color = '0E8BDE'

    style = req.params.get('style')
    if not style:
        style = 'World_Topo_Map'
    if style not in BASEMAPS.keys():
        style = 'World_Topo_Map'

    height = req.params.get('height')
    if not height:
        height = 600

    width = req.params.get('width')
    if not width:
        width = 800

    zip = req.params.get('zip')
    if not zip:
        return func.HttpResponse(
            body=json.dumps({'detail': 'Zip list is empty'}),
            status_code=404, mimetype="application/json",)

    union = req.params.get('union')

    if not union:
        union = False
    else:
        try:
            union = bool(int(union))
            logging.info(union)
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({'detail': str(e)}),
                status_code=422, mimetype="application/json")

    try:
        zip_list = [int(x) for x in zip.split(',')]
        width = int(width)
        height = int(height)
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({'detail': str(e)}),
            status_code=422, mimetype="application/json")
    if len(zip_list) != 0:
        polygons = fetch_data(zip_list, union)
        img = render_map(polygons, height, width, style, color)
        try:
            return func.HttpResponse(body=img, mimetype="image/WebP")
        except Exception as e:
            return func.HttpResponse(
                body=json.dumps({'detail': str(e)}),
                status_code=404, mimetype="application/json",
            )
    else:
        return func.HttpResponse(
            body=json.dumps({'detail': "zip list is empty"}),
            status_code=404, mimetype="application/json",

        )
