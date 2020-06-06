#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 25 09:42:46 2018

@author: chrispedder
"""

from tweet_dumper import get_all_tweets
from api_key_secrets import GOOGLE_API_KEY

import pandas as pd
import numpy as np
import csv
import time
import re

# geotext for spotting city names in strings, geocoder for getting latitude
# and longitude data from city names
from geotext import GeoText
from geopy.geocoders import GoogleV3

# folium for plotting nice, interactive html maps
import folium

# import argparse to handle user input
import argparse

def is_retweet(row):
    if row['text'][2:4] == 'RT':
        return True
    else:
        return False

def drop_retweets(dataframe):
    dataframe['Retweet'] = dataframe.apply (lambda row: is_retweet(row),axis=1)
    dataframe = dataframe[dataframe['Retweet'] == False]
    dataframe.drop(['Retweet'], axis=1, inplace = True)
    return dataframe


def remove_groups(string):

    string = re.sub(r'\\xe2\\\w{3}\\\w{3}','\'',string,re.U)

    string = re.sub(r'\\xf0\\\w{3}\\\w{3}\\\w{3}','',string,re.U)

    string = re.sub(r'\\n','',string,re.U)

    string = re.sub(r'&lt;&lt;','',string,re.U)

    string = re.sub(r'&gt;&gt;','',string,re.U)

    string = re.sub(r'&amp;','\&',string,re.U)

    return string[1:]

def clean_text(dataframe):
    dataframe['Cleaned_text'] = dataframe['text'].map(remove_groups)
    # Remove annoying unicode characters
    dataframe.drop(['text', 'tweet latitude', 'tweet longitude'], axis=1,
                   inplace = True)
    return dataframe


def add_mentioned_cities(dataframe):
    cities = []
    for text in dataframe['Cleaned_text']:
        new_cities = GeoText(text).cities

        if new_cities != []:
            cities.append(new_cities)
        else:
            cities.append(np.nan)


    city_df = pd.DataFrame({'cities_mentioned':cities})
    df_wloc = pd.merge(dataframe, city_df, left_index = True,
                       right_index = True)

    df_wloc2 = df_wloc.drop(['id'], axis = 1)
    df_wloc2 = df_wloc2.dropna(subset = ['cities_mentioned'])
    df_wloc2.reset_index(inplace=True)
    df_wloc2.drop('index',axis = 1,inplace=True)


    return df_wloc2


# Define function to query if 'latlonsfile.csv' exists, and if not to
# create it...
def file_exists(fn):
    try:
        file = open(fn, 'r')
    except FileNotFoundError:
        file = open(fn, 'w')

# Define a function to create a list of cities from the dataframe, and to
# compare them to a list of existing cities in the latlons database. Returns
# a list of new cities to lookup with the google API,
def get_new_city_lookups(dataframe, filename):

    # check filename exists, if not create an empty csv file
    file_exists(filename+'.csv')

    # get sorted list of cities in the dataframe
    listing = [item for sublist in dataframe['cities_mentioned'] for
               item in sublist]
    list_of_cities = sorted(set(listing))

    # Read existing 'latlonsfile.csv' file of queried cities
    cities_list = pd.read_csv(filename+'.csv', names = ["City",'Place',
                                                        "Lat", "Lon"])
    old_cities = list(cities_list.City)

    # Create list of cities which are not in 'latlonsfile.csv', but which were
    # mentioned by the user to then query the google api for their lat-lons
    lookups = []
    for city in list_of_cities:
        if city not in old_cities:
            lookups.append(city)

    return lookups


geolocator = GoogleV3(api_key = GOOGLE_API_KEY)
# add unique, store requests - dictionary
# delay layoff for timeout - exponential backoff for apis

def latlon(city, sleep_time = 5):
    time.sleep(sleep_time)
    try:
        place, (lat, lng) = geolocator.geocode(city,timeout=15)
    except:
        place = np.nan
        lat = np.nan
        lng = np.nan
    output = [city, place, lat, lng]
    return output


# Define a function which will update the list of lattitudes and longitudes
# with new values for this user
def lat_lon_updater(lookups,filename):

    #check that there is something to update with, i.e. that lookups not empty
    if lookups:

    # Systematically query the google api for the latitudes and longitudes
    # of places in 'lookups' list...
        list_of_latlons = []
        for elt in lookups:
            list_of_latlons.append(latlon(elt))

        # open in 'a' - append mode since we already made sure file exists
        with open(filename+".csv", "a") as file:
            writer = csv.writer(file)
            # write new lookups to file to avoid querying API in future...
            writer.writerows(list_of_latlons)


# Define function to add the latitude and longitude of mentioned cities to
# the dataframe.
def add_latlons_to_dataframe(dataframe, filename, screen_name):

    # Read in dictionary data as dataframe
    latlondf = pd.read_csv(filename+'.csv', names = ["City",'Place',
                                                     "Lat", "Lon"])
    latlondf.drop('Place',axis=1,inplace=True)

    indexer = []
    lat_coords = []
    lon_coords = []

    for j in dataframe.index:
        entry = dataframe.cities_mentioned.iloc[j]
        for i in range(len(entry)):
            indexer.append(j)
            lat_coords.append(list(latlondf[latlondf['City'] ==
                                            entry[i]]['Lat'])[0])
            lon_coords.append(list(latlondf[latlondf['City'] ==
                                            entry[i]]['Lon'])[0])

    df_coords = pd.DataFrame({'entry_number':indexer, 'lat_coord':lat_coords,
                              'lon_coord':lon_coords})

    df_reindex = dataframe.reset_index().reset_index().drop('index', axis=1)
    df_reindex.rename(columns = {'level_0':'entry_number'}, inplace = True)

    df_map = pd.merge(df_coords, df_reindex[['entry_number','created_at',
                                             'Cleaned_text']],
                      how='left', on= 'entry_number')

    # save copy of coordinates and tweets to csv
    df_map.to_csv('map_coords_'+screen_name, sep=',')

    # drop all NaN entries in latitude/longitude coords
    # (these come from google api timeouts)
    df_map_nonan = df_map.dropna(subset = ['lat_coord'])

    return df_map_nonan

### Create an interactive .html mapping with Folium

def create_folium_map(dataframe, latitude, longitude, screen_name):

    tmap=folium.Map(location = [latitude, longitude], zoom_start = 6,
                    tiles = 'OpenStreetMap')

    fg = folium.FeatureGroup(name = "Tweet Locations")

    for lat, lon, text, timecr in zip(dataframe['lat_coord'],
                                      dataframe['lon_coord'],
                                      dataframe['Cleaned_text'],
                                      dataframe['created_at']):
        fg.add_child(folium.Marker(location = [lat,lon], popup =
                                   (folium.Popup(text+' '+str(timecr),
                                                 parse_html = True)),
                                                 icon=folium.Icon(color =
                                                                  'green',
                                                                  icon_color =
                                                                  'green')))
    tmap.add_child(fg)

    tmap.add_child(folium.LayerControl())
    tmap.save(outfile=screen_name+'_map.html')

def Main():
    # Define user screen name to dowload tweets for
    parser = argparse.ArgumentParser()
    parser.add_argument('screen_name', help='The screen name of the person\
                        whose tweets you want to map', type=str)
    args = parser.parse_args()

    screen_name = args.screen_name

    # Download all the 3200 last tweets for screen name
#    get_all_tweets(screen_name)

    # Read csv file created by tweet scraper for person of interest
    df = pd.read_csv(screen_name+'_tweets.csv')

    # drop all retweets from dataframe
    df = drop_retweets(df)

    # clean text of unicode characters
    clean_df = clean_text(df)

    # find all tweets containing the names of cities, extract these names to
    # a new column
    cities_df = add_mentioned_cities(clean_df)

    print(cities_df.head(20))
    lookups = get_new_city_lookups(cities_df, 'latlons')

    lat_lon_updater(lookups, 'latlons')
    # Reset the lookups variable to be an empty list
    lookups = []

    df_map = add_latlons_to_dataframe(cities_df, 'latlons', screen_name)
    print(df_map.head(20))
    # generate map
    latitude = 0
    longitude = 30
    create_folium_map(df_map, latitude, longitude, screen_name)

    return

if __name__ == '__main__':
    Main()
