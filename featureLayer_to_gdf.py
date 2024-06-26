import os
import requests
import configparser
import pandas as pd
import geopandas as gpd

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
    response = requests.post(TOKEN_URL, data=params)
    response.raise_for_status()  
    return response.json().get('token')

def query_feature_layer(ACCOUNT_ID, FEATURE_LAYER, token):
    query_url = f"https://services6.arcgis.com/{ACCOUNT_ID}/arcgis/rest/services/{FEATURE_LAYER}/FeatureServer/0/query"
    query_params = {
        'where': '1=1',  # Return all features
        'outFields': '*',  # Return all fields
        'returnGeometry': 'true',
        'geometryPrecision': 6,
        'outSR': 4326,  # WGS84 coordinate system
        'f': 'json',
        'token': token
    }
    response = requests.get(query_url, params=query_params)
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    return response.json()

def features_to_geodataframe(features):
    # Extract features from the JSON response
    features_list = features['features']
    
    # Create a list to store the data
    data = []
    
    for feature in features_list:
        attributes = feature['attributes']
        geometry = feature['geometry']
        
        # Convert the geometry to WKT format
        if 'rings' in geometry:  # Polygon
            wkt_geom = f"POLYGON({','.join([' '.join([f'{x} {y}' for x, y in ring]) for ring in geometry['rings']])})"
        elif 'paths' in geometry:  # LineString
            wkt_geom = f"LINESTRING({','.join([f'{x} {y}' for x, y in geometry['paths'][0]])})"
        elif 'points' in geometry:  # MultiPoint
            wkt_geom = f"MULTIPOINT({','.join([f'{x} {y}' for x, y in geometry['points']])})"
        else:  # Point
            wkt_geom = f"POINT({geometry['x']} {geometry['y']})"
        
        attributes['geometry'] = wkt_geom
        data.append(attributes)
    
    # Create a DataFrame
    df = pd.DataFrame(data)
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=gpd.GeoSeries.from_wkt(df['geometry']), crs='EPSG:4326')
    
    return gdf

if __name__ == "__main__":
    # User credentials and feature layer ID
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.ini')
    config = read_config(config_path)
    
    TOKEN_URL = config.get('ago', 'token_url')
    HOST = config.get('ago', 'host')
    USERNAME = config.get('ago', 'username')
    PASSWORD = config.get('ago', 'password')
    ACCOUNT_ID = config.get('ago', 'account_id')
    
    # Get token
    token = get_token(TOKEN_URL, HOST, USERNAME, PASSWORD)
    
    FEATURE_LAYER = "TEST_data_CWD_no_private_info"
    features = query_feature_layer(ACCOUNT_ID, FEATURE_LAYER, token)
    
    # Convert features to GeoDataFrame
    gdf = features_to_geodataframe(features)
    