import os
import requests
import configparser
import pandas as pd
import geopandas as gpd
from shapely import geometry

def read_config(config_file):
    """Reads the configuration file without interpolation."""
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_file)
    
    return config


def get_token(TOKEN_URL, HOST, USERNAME, PASSWORD):
    params = {
        'username': USERNAME,
        'password': PASSWORD,
        'referer': HOST,
        'f': 'json'
    }
    #response = requests.post(TOKEN_URL, data=params, verify=False) #without SSL verification
    response = requests.post(TOKEN_URL, data=params, verify=True)  #with SSL verification
    response.raise_for_status()  
    
    return response.json().get('token')


def query_feature_layer(ACCOUNT_ID, FEATURE_SERVICE, LYR_INDEX, token):
    """Returns data from AGO layer based on query """
    query_url = f"https://services6.arcgis.com/{ACCOUNT_ID}/arcgis/rest/services/{FEATURE_SERVICE}/FeatureServer/{LYR_INDEX}/query"
    query_params = {
        'where': '1=1',  # Return all features
        'outFields': '*',  # Return all fields
        'returnGeometry': 'true',
        'geometryPrecision': 6,
        'outSR': 4326,  # WGS84 coordinate system
        'f': 'json',
        'token': token
    }
    response = requests.get(query_url, params=query_params, verify=False) #without SSL verification
    #response = requests.get(query_url, params=query_params, verify=True)   #with SSL verification
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    return response.json()

def features_to_geodataframe(features):
    features_list = features['features']
    data = []
    
    for feature in features_list:
        attributes = feature['attributes']
        geom = feature['geometry']
        
        # Convert ESRI JSON to GeoJSON
        if 'rings' in geom:
            geom_type = "Polygon"
            coordinates = geom['rings']
        elif 'paths' in geom:
            geom_type = "LineString"
            coordinates = geom['paths'][0]
        elif 'points' in geom:
            geom_type = "MultiPoint"
            coordinates = geom['points']
        else:
            geom_type = "Point"
            coordinates = [geom['x'], geom['y']]
        
        geojson = {
            "type": geom_type,
            "coordinates": coordinates
        }
        
        # Create Shapely geometry from GeoJSON
        shape = geometry.shape(geojson)
        
        attributes['geometry'] = shape
        data.append(attributes)
    
    gdf = gpd.GeoDataFrame(data, geometry='geometry', crs=4326)
    
    return gdf



if __name__ == "__main__":
    # User credentials and feature layer ID
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config = read_config(config_path)
    
    print('Reading configuration from file')
    TOKEN_URL = config.get('ago', 'token_url')
    HOST = config.get('ago', 'host')
    USERNAME = config.get('ago', 'username')
    PASSWORD = config.get('ago', 'password')
    ACCOUNT_ID = config.get('ago', 'account_id')
    

    print('Getting AGOL Token')
    token = get_token(TOKEN_URL, HOST, USERNAME, PASSWORD)
    
    print('Retrieving data from AGOL')
    FEATURE_SERVICE = "TEST_data_CWD_no_private_info"
    LYR_INDEX= 0
    features = query_feature_layer(ACCOUNT_ID, FEATURE_SERVICE, LYR_INDEX, token)
    
    print('Converting data to geodataframe')
    gdf = features_to_geodataframe(features)

    print (gdf.head())