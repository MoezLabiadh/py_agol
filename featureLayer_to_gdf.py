import os
import requests
import configparser
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Point

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
    #response = requests.get(query_url, params=query_params, verify=False) #without SSL verification
    response = requests.get(query_url, params=query_params, verify=True)   #with SSL verification
    response.raise_for_status()  # Raise an exception for HTTP errors
    
    return response.json()


def features_to_geodataframe(features_json):
    """Converts features JSON to a GeoDataFrame."""
    features = features_json['features']
    data = []
    for feature in features:
        attributes = feature['attributes']
        geometry = feature.get('geometry')
        if geometry:
            if 'x' in geometry and 'y' in geometry:
                geom = Point(geometry['x'], geometry['y'])
            else:
                geom = shape(geometry)
            attributes['geometry'] = geom
        else:
            attributes['geometry'] = None
        data.append(attributes)
    
    df = pd.DataFrame(data)
    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    
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
    FEATURE_LAYER = "TEST_data_CWD_no_private_info"
    features = query_feature_layer(ACCOUNT_ID, FEATURE_LAYER, token)
    
    print('Converting data to geodataframe')
    gdf = features_to_geodataframe(features)

    print (gdf.head())