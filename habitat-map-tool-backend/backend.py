from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from raster import rasterize_layer, print_raster
import geopandas as gpd
from shapely.geometry import box
from load_data import DataService
import time
import math
import json
import os

data_path = '../data/'
LEVELS_DIR = '../levels'
MAIN_CRS = 'EPSG:4326'

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}},
     allow_headers=['Content-Type', 'Access-Control-Allow-Origin', 'Access-Control-Allow-Headers'],
     supports_credentials=True)

data_service = DataService()


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.before_request
def before_request():
    headers = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Credentials': 'true',
               'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
               'Access-Control-Allow-Headers': 'Content-Type'}
    if request.method.lower() == 'options':
        return jsonify(headers), 200
    

@app.route('/levels', methods=['GET'])
def list_levels():
    levels = []
    for level_name in os.listdir(LEVELS_DIR):
        level_path = os.path.join(LEVELS_DIR, level_name)
        if os.path.isdir(level_path):
            metadata_path = os.path.join(level_path, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    levels.append(metadata)
            else:
                levels.append({"level_name": level_name})
    return jsonify(levels)





@app.route('/process', methods=['GET', 'POST', 'OPTIONS'])
@cross_origin()
def process_data():

    
    if request.method == 'OPTIONS' or request.method == 'GET':
        return jsonify({'some': 'data'}), 200
    

    if (not data_service.data_loaded):
        data_service.load_base_data()

    data = request.get_json()

    x = data['centerPoint'][1]
    y = data['centerPoint'][0]
    height = data['boundHeight']
    name = data['name']


    ##check to see if the name is in the levels directory
    level_path = os.path.join(LEVELS_DIR, name)
    if not os.path.exists(level_path):
        # create the level directory
        os.makedirs(level_path)
    
    # create the metadata file
    metadata = {
        "name": name,
        "id": name,
        "centerPoint": data['centerPoint'],
        "boundHeight": data['boundHeight'],
        "hasBeenProcessed": False
    }
    metadata_path = os.path.join(level_path, 'metadata.json')
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata,f,indent=4)
            
    level_path = os.path.join(LEVELS_DIR, name)

    start = time.time()
    start_time = start
    with open('../constants.json') as f:
        constants = json.load(f)['constants']

        miny = y - height
        maxy = y + height
        minx = x - height / math.cos(y * math.pi/180)
        maxx = x + height / math.cos(y * math.pi/180)
        
        resolution = 15 / 111000

        bounding_box = gpd.GeoDataFrame({'geometry': [box(minx, miny, maxx, maxy)]}, crs=MAIN_CRS)

        start_time = time.time()    
        soils_gdf = data_service.load_soil_data(bounding_box)
        print("Soil data loaded")
        water_gdf = data_service.load_water_data(bounding_box)
        print("Water data loaded")
        
        # DEM (already rasterized)
        dem_raster = data_service.load_dem_data(bounding_box, resolution)
        print("DEM data loaded")



        precip_raster = rasterize_layer(soils_gdf, 'map_r', resolution)
        temp_raster = rasterize_layer(soils_gdf, 'airtempa_r', resolution)
        soil_raster = rasterize_layer(soils_gdf, 'taxorder', resolution, constants['soil_type_mapping'])
        water_raster = rasterize_layer(water_gdf, 'qa', resolution)
        print("Rasterization complete")

        print_raster(dem_raster, 'dem', level_path)
        print_raster(precip_raster, 'precip', level_path)
        print_raster(temp_raster, 'temp', level_path)
        print_raster(soil_raster, 'soil', level_path)
        print_raster(water_raster, 'water', level_path)
        print ("Total time: {}".format(time.time() - start_time))
    response = jsonify({'some': 'data'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response





if __name__ == '__main__':
    app.run(debug=True)