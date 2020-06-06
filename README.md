# tweet_city_mentions
A short personal project to see if I could map the places people were tweeting about.

Tweet scraping project documentation

## Aim.

The objective of this project it to write a short workbook that will allow the user to download the data from a target?s (public) twitter account, and analyse it to find the date, time and location of places they have visited. Initial objective is to do this for English-language users, before moving on to do similar analysis for Russian-language targets.

## Setup.

The analysis code is designed for use with python 3.6. Additional packages required for this installation are:

Pandas
Numpy
Requests
Matplotlib

Geotext (installed by command line: sudo pip install geotext)
Transliterate (installed by command line: sudo pip install transliterate)
CSV
Re
Folium

(see requirements.txt)

Additionally, the modified tweet_dumper.py file from (https://gist.github.com/yanofsky/5436496) is needed. This function is nicely documented in the book ?Mastering Social Media Mining with Python? by Marco Bonzanini (Packt 2016), and on his website (https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/ ). The modified function can deal with the newer 280char tweets available since November 2017.

TODO - this function needs to be updated to deal with utf-8 encoding of non-ASCII characters, so that we can scrape tweets from e.g. Russian and Chinese character sets.

## Implementation.

In the process of initial testing, it became clear that there can be serious problems with false-positives. An example of this would be a user tweeting ?Good luck to @FCBarcelona?. The geopy algorithm will spot this as a mention of Barcelona, but there is little likelihood that the user is actually located there. False negatives are rarer, and tend to occur when the geopy module has too many towns to choose between (e.g. ?Newton?, which should return many towns in the UK, but the one return is for a city in the US). This can be mitigated by restricting the search area to a geographic domain within the guppy module.

To deal with this problem of false positives, early in the project I resolved to plot the data graphically on a map, in order that we can see places of interest, and then check the text and date of the tweet to see if it constitutes a ?hit? for the planned investigation.

The best approach for producing interactive html maps in python is Folium, which allows us to choose an accurate basemap, and then plot markers with included text data on a second, removable layer.

## API keys needed.

In order to run this scraper, we need two different APIs (Application programming interfaces). The first is the twitter API, which requires i) that we have a twitter account (it doesn't have to be our own, or one that is used), and ii) that we register as an app developer at http://apps.twitter.com. To quote from Marco Bonzanini's page "You will receive a 'consumer key' and a 'consumer secret': these are application settings that should always be kept private. From the configuration page of your app, you can also require an access token and an access token secret. Similarly to the consumer keys, these strings must also be kept private: they provide the application access to Twitter on behalf of your account."

The second API we need is a google maps api. This requires I) a google account and ii) that we register as a developer. The signup procedure is well documented here: https://developers.google.com/maps/documentation/geocoding/start

## Usage.

Usage is (I hope!) pretty straightforward. Enter the username of the person whose tweets you would like to map in the second box. From then on, you should be able to run every cell without issue. The script will write several files to the folder where you saved it, don?t panic! The main output is a map called 'username_map.html'. Open this in a browser when connected to the internet, and you will be able to see the tweet map.

## Non-latin (in dev.)

It looks like it will be necessary to change the format of the tweet scraping function to deal with non ASCII characters (which unfortunately includes accented letters, like in Seàn ;) ). I have been experimenting with formatting this, but unfortunately with little success so far. On the plus side, I'm learning more than anyone wants to know about text encoding!
