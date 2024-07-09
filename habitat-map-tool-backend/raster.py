import geopandas as gpd
from shapely.geometry import box
from rasterio.transform import from_origin
from rasterio.features import rasterize
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from util import get_elapsed_time


def normalize_raster(raster_data):
    raster_min = np.nanmin(raster_data)
    raster_max = np.nanmax(raster_data)
    print("Min: {}, Max: {}".format(raster_min, raster_max))
    if (raster_max == raster_min):
        raster_data_normalized =  raster_data
    else:
        raster_data_normalized = (raster_data - raster_min) / (raster_max - raster_min)
    raster_data_normalized = (raster_data_normalized * 255).astype(np.uint8)
    return raster_data_normalized

def rasterize_layer(gdf, layer_name, resolution, attribute_mapping = None):
    xmin, ymin, xmax, ymax = gdf.total_bounds
    width = int((xmax - xmin) / resolution)
    height = int((ymax - ymin) / resolution)
    transform = from_origin(xmin, ymax, resolution, resolution)
    raster_data = np.full((height, width), np.nan)
    # Rasterize the clay content
    for _, row in gdf.iterrows():
        
        value = 0
        if layer_name == 'water':
            value = 1
        else:
            value = row[layer_name]
            if value is None:
                value = np.nan
            elif attribute_mapping:
                value = attribute_mapping[value]    

        shapes = [(row['geometry'], value)]

        burned = rasterize(
            shapes=shapes,
            out_shape=(height, width),
            fill=np.nan,
            transform=transform,
            all_touched=True,
            dtype='float32'
        )
        raster_data = np.where(np.isnan(raster_data), burned, raster_data)
    print("Successfully rasterized layer: {} {}".format(layer_name, get_elapsed_time()))
    return raster_data

def print_raster(raster_data, title, output_dir):
    normalized_raster = normalize_raster(raster_data)
    
    plt.imsave('{}/{}.png'.format(output_dir, title), normalized_raster, cmap='gray', vmin=0, vmax=255)

    print("Successfully created raster: {}".format(title))
