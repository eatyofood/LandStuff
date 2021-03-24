import os
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
# Get Adress 
## NOTE: its not getting acurate addresses
### couple of things to try
# - running the raw coordinates through Nominatum
# - using a differnt geocoder

import pandas as pd

import geopandas as gpd
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

import matplotlib.pyplot as plt
import plotly_express as px
import tqdm
from tqdm import tqdm
from tqdm._tqdm_notebook import tqdm_notebook



class ImageMetaData(object):
    '''
    Extract the exif data from any image. Data includes GPS coordinates, 
    Focal Length, Manufacture, and more.
    '''
    exif_data = None
    image = None

    def __init__(self, img_path):
        self.image = Image.open(img_path)
        #print(self.image._getexif())
        self.get_exif_data()
        super(ImageMetaData, self).__init__()

    def get_exif_data(self):
        """Returns a dictionary from the exif data of an PIL Image item. Also converts the GPS Tags"""
        exif_data = {}
        info = self.image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    gps_data = {}
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_data[sub_decoded] = value[t]

                    exif_data[decoded] = gps_data
                else:
                    exif_data[decoded] = value
        self.exif_data = exif_data
        return exif_data

    def get_if_exist(self, data, key):
        if key in data:
            return data[key]
        return None

    def convert_to_degress(self, value):

        """Helper function to convert the GPS coordinates 
        stored in the EXIF to degress in float format"""
        d0 = value[0][0]
        d1 = value[0][1]
        d = float(d0) / float(d1)

        m0 = value[1][0]
        m1 = value[1][1]
        m = float(m0) / float(m1)

        s0 = value[2][0]
        s1 = value[2][1]
        s = float(s0) / float(s1)

        return d + (m / 60.0) + (s / 3600.0)

    def get_lat_lng(self):
        """Returns the latitude and longitude, if available, from the provided exif_data (obtained through get_exif_data above)"""
        lat = None
        lng = None
        exif_data = self.get_exif_data()
        #print(exif_data)
        if "GPSInfo" in exif_data:      
            gps_info = exif_data["GPSInfo"]
            gps_latitude = self.get_if_exist(gps_info, "GPSLatitude")
            gps_latitude_ref = self.get_if_exist(gps_info, 'GPSLatitudeRef')
            gps_longitude = self.get_if_exist(gps_info, 'GPSLongitude')
            gps_longitude_ref = self.get_if_exist(gps_info, 'GPSLongitudeRef')
            #
            # CUT THIS OFF AT THE END AND YOU MIGHT GET A MORE ACURATE ADDRESS ...
            #
            if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
                lat = self.convert_to_degress(gps_latitude)
                if gps_latitude_ref != "N":                     
                    lat = 0 - lat
                lng = self.convert_to_degress(gps_longitude)
                if gps_longitude_ref != "E":
                    lng = 0 - lng
        return lat, lng

    
    
'''
STEP ONE: GET DATA OUT OF PICTURES
'''
# name directory and isolate jpegs


path = 'photos/'
dili = os.listdir(path)
dili = [p for p in dili if '.jpg' in p ]
pd.DataFrame(dili)


# extract coorinats fom each picture and add to a data frame

### basically i can just put all of this into a dictionary 

picture   = 0
li        = []
for picture in range(len(dili)):
    #loop starts here
    path_name = path + dili[picture]
    print(path_name)

    meta_data =  ImageMetaData(path_name)
    latlng =meta_data.get_lat_lng()
    print(latlng)

    exif_data = meta_data.get_exif_data()
    #print(exif_data)
    lat = latlng[0]
    lon = latlng[1]

    print(lat)
    print(lon)

    print(' ')

    di = {}
    di['path_name'] = path_name
    di['latlng']    = latlng
    di['LAT']       = lat
    di['LON']       = lon
    li.append(di)

df = pd.DataFrame(li)



'''
STEP TWO: GET ADDRESSES 
'''
# GeoCoding Portion
locator = Nominatim(user_agent="myGeocoder", timeout=10)
rgeocode = RateLimiter(locator.reverse, min_delay_seconds=0.001)
rgeocode

#this applys the geocoder to the dataframe 
df['address'] = df['latlng'].apply(rgeocode)




df

pd.set_option('display.max_colwidth',None)

# name the csv and save it

from datetime import datetime



# name for directory and create it if it doent exist
save_path = 'Addresses/'
if not os.path.exists(save_path):
    os.mkdir(save_path)

#name for csv
save_name = save_path +str(datetime.now()).split('.')[0].replace(' ','_') + '.csv'
print(save_name)


df.to_csv(save_name,index=False)



# MIX ALL MAPS TOGETHER AND DROP DUPLICATES



'''
STEP: THREE - CREATE A MAP FILE 
'''

import folium
import pandas
import pretty_errors

#DATA DATA DATA
#data = pandas.read_csv("Addresses/2021-02-24_13:56:17.csv") # -- HERE
# LOAD ALL THE DATA AND MIX IT TOGETHER

import pandas as pd
import os 

os.listdir()

path = 'Addresses/'
adli = os.listdir(path)
pd.DataFrame(adli)



# Mix All the DataFrames Together


#use the first sheet as a refrence
first_sheet   = path + adli[0]
adf           = pd.read_csv(first_sheet)
#then append...
if len(adli)  > 1:
    for i in range(1,len(adli)):
        sheet = path + adli[i]
        newdf = pd.read_csv(sheet)
        adf   = adf.append(newdf)
        adf   = adf.drop_duplicates()
#mixed and happy
data          = adf.copy()

data

if 'Unnamed: 0' in data.columns:
    data = data.drop('Unnamed: 0',axis=1)
print(len(data))
data = data.drop_duplicates()
print(len(data))




lat = list(data["LAT"])
lon = list(data["LON"])
adr = list (data['address'])


# THIS CAN BECOME DISTANCE BASED. 

#elev = list(data[""])

def color_producer(elevation):
    if elevation < 1000:
        return 'green'
    elif 1000 <= elevation < 3000:
        return 'orange'
    else:
        return 'red'

map = folium.Map(location=[38.58, -99.09], zoom_start=6)#, tiles="Mapbox Bright")

fgv = folium.FeatureGroup(name="Pictures")

for lt, ln,ad in zip(lat, lon,adr):
    fgv.add_child(folium.CircleMarker(location=[lt, ln], radius = 6, popup=str(ad)))#,
    #fill_color=color_producer(el), fill=True,  color = 'grey', fill_opacity=0.7))

''' THESE ARE EXTRA FEATURES WHICH I AM JUST GOING TO IGNORE FOR NOW'''

#fgp = folium.FeatureGroup(name="Population")
#
#fgp.add_child(folium.GeoJson(data=open('world.json', 'r', encoding='utf-8-sig').read(),
#style_function=lambda x: {'fillColor':'green' if x['properties']['POP2005'] < 10000000
#else 'orange' if 10000000 <= x['properties']['POP2005'] < 20000000 else 'red'}))

map.add_child(fgv)
#map.add_child(fgp)
#map.add_child(folium.LayerControl())

map.save("Map.html")


# LAUNCH THE MAP!!!
'''
STEP FOUR: LAUNCH WEBMAP
'''
import webbrowser
new = 2 # open in a new tab, if possible

#// open a public URL, in this case, the webbrowser docs
url = 'Map.html'
webbrowser.open(url,new=new)
