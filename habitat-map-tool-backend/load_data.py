import geopandas as gpd
from shapely.geometry import Point, box
import rasterio
from rasterio.transform import from_origin, Affine
from rasterio.features import rasterize
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from util import get_elapsed_time

SOILDB_PATH = '../data/SSURGODB.gpkg' 
DEM_PATH = '../data/merged_dem.tif'
WATERDB_PATH = '../data/nhdplus_epasnapshot2022_or.gpkg'
MAIN_CRS = 'EPSG:4326'

SPATIAL_LAYER = 'mupolygon'
FLOWLINES_LAYER = 'nhdflowline_or'
WATERBODIES_LAYER = 'nhdwaterbody_or' 
EROMMA_LAYER = 'nhdpluseromma_or'

class DataService:
    def __init__(self):
        self.spatial_gdf = None
        self.flowlines_gdf = None
        self.waterbodies_gdf = None
        self.eromma_df = None
        self.data_loaded = False


    def load_base_data(self):
        # Connect to the SQLite database and load relevant tables
        conn = sqlite3.connect(SOILDB_PATH)
        self.component_df = pd.read_sql_query("SELECT mukey, taxorder, map_l, map_r, map_h, airtempa_l, airtempa_r, airtempa_h FROM component", conn)
        conn.close()
        print("Load tabular soil data from database {}".format(get_elapsed_time()))

        self.spatial_gdf = gpd.read_file(SOILDB_PATH, layer=SPATIAL_LAYER)
        print("Load soil data from file {}".format(get_elapsed_time()))

        self.flowlines_gdf = gpd.read_file(WATERDB_PATH, layer=FLOWLINES_LAYER)
        self.waterbodies_gdf = gpd.read_file(WATERDB_PATH, layer=WATERBODIES_LAYER)
        self.eromma_df = gpd.read_file(WATERDB_PATH, layer=EROMMA_LAYER)
        print("Load water data from file {}".format(get_elapsed_time()))
        self.data_loaded = True

    def load_soil_data(self, bounding_box):
        merged_gdf = self.spatial_gdf.merge(self.component_df, on='mukey')
        bounding_box_gdf = bounding_box.to_crs(merged_gdf.crs)
        merged_gdf = gpd.overlay(merged_gdf, bounding_box_gdf, how='intersection')
        print("Soil Data Processed. {}".format(get_elapsed_time()))
        return merged_gdf

    def load_dem_data(self, bounding_box, resolution):
        with rasterio.open(DEM_PATH) as src:
            dem_crs = src.crs
            dem_transform = src.transform
            bbox_gdf = bounding_box.to_crs(dem_crs)
            bbox = bbox_gdf.total_bounds   
            dem_bounds = src.bounds
            if (bbox[0] < dem_bounds.left or bbox[2] > dem_bounds.right or
                bbox[1] < dem_bounds.bottom or bbox[3] > dem_bounds.top):
                raise ValueError("Bounding box is out of DEM bounds.")
            window = rasterio.windows.from_bounds(*bbox, transform=dem_transform)
            dem_clip = src.read(1, window=window)
            transform_clip = src.window_transform(window)

        print("DEM data clipped. {}".format(get_elapsed_time()))
        width = int((bbox[2] - bbox[0]) / resolution)
        height = int((bbox[3] - bbox[1]) / resolution)

        # Check if dimensions are valid
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid target dimensions: width={width}, height={height}")

        dem_data = np.empty((height, width), dtype=np.float32)
        dst_transform = from_origin(bbox[0], bbox[3], resolution, resolution)
        reproject(
            source=dem_clip,
            destination=dem_data,
            src_transform=transform_clip,
            src_crs=dem_crs,
            dst_transform=dst_transform,
            dst_crs=dem_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
            num_threads=1
        )
        print("DEM data reprojected. {}".format(get_elapsed_time()))
        return dem_data

    def load_water_data(self, bounding_box):
        
        eromma_df = self.eromma_df[['nhdplusid', 'qa']]
        bounding_box_gdf = bounding_box.to_crs(self.flowlines_gdf.crs)
        flowlines_gdf = gpd.overlay(self.flowlines_gdf, bounding_box_gdf, how='intersection')
        waterbodies_gdf = gpd.overlay(self.waterbodies_gdf, bounding_box_gdf, how='intersection')
        print("Filtered data for bounding box {}".format(get_elapsed_time()))

        flowlines_gdf = flowlines_gdf.merge(eromma_df, on='nhdplusid')
        print("Merged data {}".format(get_elapsed_time()))


        flowlines_gdf = flowlines_gdf.to_crs(crs=3857)
        waterbodies_gdf = waterbodies_gdf.to_crs(MAIN_CRS)
        flowlines_gdf['buffer'] = .002
        buffered_flowlines_gdf = flowlines_gdf.copy()
        buffered_flowlines_gdf['geometry'] = flowlines_gdf.buffer(buffered_flowlines_gdf['buffer'])
        print("Buffered Flowlines {}".format(get_elapsed_time()))
    
        buffered_flowlines_gdf = buffered_flowlines_gdf.to_crs(MAIN_CRS)
    
    
        # Combine the buffered flowlines with the waterbodies polygons
        combined_gdf = gpd.GeoDataFrame(pd.concat([buffered_flowlines_gdf, waterbodies_gdf], ignore_index=True))
        #combined_gdf = combined_gdf[combined_gdf.geometry.intersects(bounding_box)]
        print("Combined Flowlines and Waterbodies {}".format(get_elapsed_time()))

        return combined_gdf