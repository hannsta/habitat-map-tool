from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from raster import rasterize_layer, print_raster
from weather import get_weather_data
import geopandas as gpd
from shapely.geometry import box
from load_data import DataService
import time
import math
import json
import os
from scipy.ndimage import binary_dilation
from scipy.ndimage import convolve, distance_transform_edt
import numpy as np
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
    #convert boundHeight to meters


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
        print("Bounding box: {} {} {} {}".format(minx, miny, maxx, maxy))
        bounding_box = gpd.GeoDataFrame({'geometry': [box(minx, miny, maxx, maxy)]}, crs=MAIN_CRS)

        start_time = time.time()    
        soils_gdf = data_service.load_soil_data(bounding_box)
        print("Soil data loaded")
        water_gdf = data_service.load_water_data(bounding_box)
        print("Water data loaded")
        
        # DEM (already rasterized)
        dem_raster, dem_transform = data_service.load_dem_data(bounding_box, resolution)
        print("DEM data loaded")



        precip_raster, precip_transform = rasterize_layer(soils_gdf, 'map_r', resolution)
        silt_raster, silt_transform = rasterize_layer(soils_gdf, 'silttotal_r', resolution)
        clay_raster, clay_transform = rasterize_layer(soils_gdf, 'claytotal_r', resolution)
        sand_raster, sand_transform = rasterize_layer(soils_gdf, 'sandtotal_r', resolution)
        organic_raster, organic_transform = rasterize_layer(soils_gdf, 'om_r', resolution)
        rock_raster, rock_transform = rasterize_layer(soils_gdf, 'fragvol_r', resolution)
        temp_raster, temp_transform = rasterize_layer(soils_gdf, 'airtempa_r', resolution)
        soil_raster, soil_transform = rasterize_layer(soils_gdf, 'taxorder', resolution, constants['soil_type_mapping'])
        water_raster, water_transform = rasterize_layer(water_gdf, 'water', resolution)
        print("Rasterization complete")
        water_raster[dem_raster <= 0] = 1

        kernel = np.ones((3,3), dtype=int)
        # Convolve the water layer with the kernel to count surrounding water pixels
        water_count = convolve(water_raster, kernel, mode='constant', cval=0)

        def adjust_height(water_count, base_depth=0, max_depth=20, max_count=9):
                        
            scaling_factor = (water_count * water_count) / (max_count * max_count)
            return np.clip(scaling_factor * (max_depth - base_depth) + base_depth, 0, max_depth)


        # Apply the adjustment
        depth_adjustment = adjust_height(water_count)
        adjusted_dem = dem_raster.copy()
        adjusted_dem[water_raster == 1] -= depth_adjustment[water_raster == 1]



        def buffer_raster_with_gradient(water_raster, buffer_distance, pixel_size):
            buffer_size = int(buffer_distance / pixel_size)
            water_mask = water_raster == 1
            distance = distance_transform_edt(~water_mask)
            gradient = np.clip(1 - distance / buffer_size, 0, 1)
            buffered_raster = np.where(water_mask, 1, gradient)
            water_raster[:] = buffered_raster

        def buffer_flood_zone_raster(water_raster, dem_raster, buffer_distance, pixel_size, max_elevation_diff):
            buffer_size = int(buffer_distance / pixel_size)
            water_mask = water_raster == 1
            
            # Compute the distance transform
            distance = distance_transform_edt(~water_mask)
            
            # Compute the elevation gradient
            elevation_diff = np.abs(dem_raster - np.min(dem_raster[water_mask]))
            elevation_factor = np.clip(elevation_diff / max_elevation_diff, 0, 1)
            
            # Combine distance and elevation to create a gradient
            gradient = np.clip(1 - (distance / buffer_size) * elevation_factor, 0, 1)
            buffered_raster = np.where(water_mask, 1, gradient)
            
            return buffered_raster

        # Example usage
        # Assuming water_raster is already defined and contains your raster data
        buffer_distance = 3  # Buffer distance in meters
        flood_buffer_distance = 5
        pixel_size = 1  # Assuming each pixel represents 1 meter (adjust if needed)
        max_elevation_diff = 50

        # Update the water_raster in place
        flood_raster = buffer_flood_zone_raster(water_raster, dem_raster, flood_buffer_distance, pixel_size, max_elevation_diff)
        buffer_raster_with_gradient(water_raster, buffer_distance, pixel_size)

        min, max = print_raster(dem_raster, dem_transform, 'dem', level_path)
        metadata['dem'] = { 'min': min, 'max': max }
        min, max = print_raster(adjusted_dem, dem_transform, 'adjusted_dem', level_path)
        metadata['adjustedDem'] = { 'min': min, 'max': max }
        min, max = print_raster(precip_raster, precip_transform, 'precip', level_path)
        metadata['precip'] = { 'min': min, 'max': max }
        min, max = print_raster(silt_raster, silt_transform, 'silt', level_path)
        metadata['silt'] = { 'min': min, 'max': max }
        min, max = print_raster(clay_raster, clay_transform, 'clay', level_path)
        metadata['clay'] = { 'min': min, 'max': max }
        min, max = print_raster(sand_raster, sand_transform, 'sand', level_path)
        metadata['sand'] = { 'min': min, 'max': max }
        min, max = print_raster(organic_raster, organic_transform, 'organic', level_path)
        metadata['organic'] = { 'min': min, 'max': max }
        min, max = print_raster(rock_raster, rock_transform, 'rock', level_path)
        metadata['rock'] = { 'min': min, 'max': max }
        min, max = print_raster(temp_raster, temp_transform, 'temp', level_path)
        metadata['temp'] = { 'min': min, 'max': max }
        print_raster(soil_raster,soil_transform, 'soil', level_path)
        min, max = print_raster(water_raster, water_transform, 'water', level_path)
        metadata['water'] = { 'min': min, 'max': max }
        min, max = print_raster(flood_raster, water_transform, 'flood', level_path)
        metadata['flood'] = { 'min': min, 'max': max }
        
        temp_data, precip_data = get_weather_data([minx, miny, maxx, maxy])
        metadata['tempData'] = temp_data
        metadata['precipData'] = precip_data
        
        print ("Total time: {}".format(time.time() - start_time))
        metadata['hasBeenProcessed'] = True



        print(metadata)
        with open(metadata_path, 'w') as f:
            json.dump(metadata,f,indent=4)
        return jsonify(metadata)
    
    response = jsonify({'some': 'data'})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response





if __name__ == '__main__':
    app.run(debug=True)