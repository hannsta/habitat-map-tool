import geopandas as gpd
from shapely.geometry import box
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.features import rasterize
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
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
    return raster_data_normalized, raster_min.item(), raster_max.item()

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
    return raster_data, transform

def print_raster(raster_data, src_transform, title, output_dir):
    # Define the target CRS
    target_crs = 'EPSG:32610'
    src_crs='EPSG:4326'
    # Create the source transform if not provided
    #src_transform = from_origin(0, 0, 1, 1)  # Assuming a default transform

    # Create a temporary file to store the reprojected raster
    temp_raster = './tmp/temp_raster.tif'
    
    # Save the input numpy array to a temporary raster file
    with rasterio.open(
        temp_raster, 'w',
        driver='GTiff',
        height=raster_data.shape[0],
        width=raster_data.shape[1],
        count=1,
        dtype=raster_data.dtype,
        crs=src_crs,
        transform=src_transform,
    ) as dst:
        dst.write(raster_data, 1)
    
    # Reproject the raster
    reprojected_raster = './tmp/reprojected_raster.tif'
    with rasterio.open(temp_raster) as src:
        transform, width, height = calculate_default_transform(
            src.crs, target_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': target_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        
        with rasterio.open(reprojected_raster, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest)

    # Load the reprojected raster
    with rasterio.open(reprojected_raster) as reprojected_src:
        reprojected_data = reprojected_src.read(1)
        normalized_raster, raster_min, raster_max = normalize_raster(reprojected_data)

        plt.imsave('{}/{}.png'.format(output_dir, title), normalized_raster, cmap='gray', vmin=0, vmax=255)

        print("Successfully created raster: {}".format(title))
        return raster_min, raster_max

# Example normalize_raster function
    # Load the reprojected raster
    with rasterio.open(reprojected_raster) as reprojected_src:
        normalized_raster, raster_min, raster_max = normalize_raster(reprojected_src.read(1))

        plt.imsave('{}/{}.png'.format(output_dir, title), normalized_raster, cmap='gray', vmin=0, vmax=255)

        print("Successfully created raster: {}".format(title))
        return raster_min, raster_max
