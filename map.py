import xml.etree.ElementTree as ET
import numpy
import json
from PIL import Image, ImageDraw


CIRCLE_RADIUS = 7

# Replicate the Hex that these values are stored at
def create_hash( internal_name, gamedata ) : 

    hash = False

    for key, value in gamedata.items() : 

        if internal_name in value : 
            hash = key
            hash = numpy.uint32( hash )
            hash = hex( hash ).rstrip("L")
            break

    return hash

location_names = {}

f=open('LocationMarker.csv')
for line in f:
    line = line.strip()
    internal_name, name = line.split(',')
    name = name.strip('"')
    location_names[internal_name] = name
f.close()

# From https://github.com/MrCheeze/botw-tools
with open( 'botw-tools/gamedata.json', 'r' ) as data :
    gamedata = json.load( data )

# Grabs in-game locations
static_values = ET.parse('Static.xml').getroot().findall('./*/value/SaveFlag/..')

botw_map = Image.open("BotW-Map.png")
map_draw = ImageDraw.Draw(botw_map)

tracked_locations = open('tracked_locations.txt')

map_locations = open('map_locations.js','w')
map_locations.write('var locations = {\n')

for line in tracked_locations:
    location = line.strip()
    found = False
    name = None
    if location in location_names:
        name = location_names[location]
    for value in static_values:
        saveflag = value.findall('./SaveFlag')[0].text
        
        if 'Location_' + location == saveflag:
            messageIDs = value.findall('./MessageID')
            if not name and len(messageIDs) and (messageIDs[0].text in location_names):
                name = location_names[messageIDs[0].text]
            if not name:
                name = location
            
            translate = value.findall('./Translate')[0]
            x,z = float(translate.attrib['X'].rstrip('f')), float(translate.attrib['Z'].rstrip('f'))
            map_locations.write('%s: {"internal_name":"%s", "display_name":"%s", "x":%g, "y":%g},\n' % ( create_hash( saveflag, gamedata ), saveflag, name, x, z ) )

            img_x = int(x/2 + 3000)
            img_y = int(z/2 + 2500)
            map_draw.ellipse((img_x-CIRCLE_RADIUS, img_y-CIRCLE_RADIUS, img_x+CIRCLE_RADIUS, img_y+CIRCLE_RADIUS), fill='cyan', outline='blue')

            found = True
            break
    if not found:
        print('Not found %s (%s)' % (location, name))

map_locations.write('};\n')

# Grabs Koroks
static_values = ET.parse('Static.xml').getroot().findall('./*/value/Flag/..')

map_locations.write('var koroks = {\n')

for value in static_values:
    flag = value.findall('./Flag')[0].text
    translate = value.findall('./Translate')[0]
    x,z = float(translate.attrib['X'].rstrip('f')), float(translate.attrib['Z'].rstrip('f'))
    map_locations.write('%s: {"internal_name":"%s", "display_name":"%s", "x":%g, "y":%g},\n' % ( create_hash( flag, gamedata ), flag, 'Korok', x, z ) )

    img_x = int(x/2 + 3000)
    img_y = int(z/2 + 2500)
    map_draw.ellipse((img_x-CIRCLE_RADIUS, img_y-CIRCLE_RADIUS, img_x+CIRCLE_RADIUS, img_y+CIRCLE_RADIUS), fill='lime', outline='green')

map_locations.write('};\n')

tracked_locations.close()
map_locations.close()

botw_map.save('BotW-Map-Labeled.png')