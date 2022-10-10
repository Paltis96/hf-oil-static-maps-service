import logging
from staticmap import StaticMap, Polygon, Line

from io import BytesIO
import json
import os

import azure.functions as func




def parse_geojosn():
    with open(f'{os.path.dirname(os.path.abspath(__file__))}/USA_Counties.json') as f:
        lines = json.loads(f.read())
    return lines


def get_polygons(geojson: dict, zips: list):
    features_list = geojson['features']
    selected_list = []
    for item in features_list:
        zip: int = int(item['properties']['FIPS'])
        if zip in zips:
            geom = item['geometry']
            if geom['type'] == 'MultiPolygon':
                for part in geom['coordinates']:
                    selected_list.append(part)
            else:
                selected_list.append(geom['coordinates'])
    return selected_list


def render_map(zips: str, width: int = 800, height: int = 600):
    img_io = BytesIO()
    m = StaticMap(width, height, 80, 80,
                  'https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', 256)

    zip_list = [int(x) for x in zips.split(',')]
    polygons = get_polygons(parse_geojosn(), zip_list)

    if len(polygons) == 0:
        return func.HttpResponse(
            "Zips not found",
            status_code=404
        )
    for coords in polygons:
        m.add_line(Line(coords[0], '#0E8BDE', 3))
        m.add_polygon(Polygon(coords[0], '#0E8BDE73', '#0E8BDE'))
    image = m.render()

    image.save(img_io, format='jpeg', quality=70)
    img_io.seek(0)

    return img_io.read()


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    headers = {"media-type": "image/jpeg"}

    zips = req.params.get('zips')
    width = req.params.get('width')
    height = req.params.get('height')

    if not zips:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            zips = req_body.get('zips')
    img = render_map(zips)
    if zips:
        return func.HttpResponse(img)
    else:
        return func.HttpResponse(
            "Zips not found",
            status_code=404
        )
