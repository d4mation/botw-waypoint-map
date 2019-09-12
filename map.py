import xml.etree.ElementTree as ET
import numpy
import json
from PIL import Image, ImageDraw
import re


CIRCLE_RADIUS = 7

# Replicate the Hex that these values are stored at
def get_hash_from_internal_name( internal_name, gamedata ) : 

    hash = False

    for key, value in gamedata.items() : 

        if internal_name in value : 
            hash = key
            hash = numpy.uint32( hash )
            hash = hex( hash ).rstrip("L")
            break

    return hash


# Korok paths are stored with each successive event being shown one after another
# We only care about ones relevant to drawing a path, so in this way we will build that data out
def findKorokPath( HashId, ActorTypes, objectReferences, results ) : 

    if ( HashId not in objectReferences ) : 
        return results

    if ( 'references' not in objectReferences[ HashId ] ) :
        return results

    name = re.sub( r"_\d*$", '', objectReferences[ HashId ]['name'] ).replace( 'MainField_', '' )

    referenceIndex = 0

    # Why did they store things so weird. Goal references Starting point, but Starting Flower references each next flower in order
    if ( name == 'FldObj_KorokGoal_A' ) : 
         referenceIndex = 2

    # We have to look back to our previous result to find the Korok in this case
    if ( name == 'FldObj_KorokStartingBlock_A' ) :

        results['path'].append( {
            'HashID': HashId,
            'references': objectReferences[ HashId ]['references'],
            'name': objectReferences[ HashId ]['name'],
            'x': objectReferences[ HashId ]['x'],
            'y': objectReferences[ HashId ]['y'],
        } )

        goalHash = results['path'][0]['HashID']
        korokHash = objectReferences[ goalHash ]['references'][1]

        return findKorokPath( korokHash, ActorTypes, objectReferences, results )

    # If we found the Korok, we've got all our data. Save the Korok reference and return
    if ( name == 'Npc_HiddenKorokFly' or name == 'Npc_HiddenKorokGround' ) : 
        
        results['korok'] = 'MainField_' + name + '_' + str( numpy.uint32( HashId ) )

        return results

    if ( len( objectReferences[ HashId ]['references'] ) == 0 ) :
        return results

    # If we are not tracking this ActorType, then skip to the next one
    try : 
        ActorTypes.index( name )
    except ValueError : 
        return findKorokPath( objectReferences[ HashId ]['references'][ referenceIndex ], ActorTypes, objectReferences, results )

    # We've got another Step. Add and return

    if ( 'path' not in results ) : 
        results['path'] = []

    results['path'].append( {
        'HashID': HashId,
        'references': objectReferences[ HashId ]['references'],
        'name': objectReferences[ HashId ]['name'],
        'x': objectReferences[ HashId ]['x'],
        'y': objectReferences[ HashId ]['y'],
    } )

    return findKorokPath( objectReferences[ HashId ]['references'][ referenceIndex ], ActorTypes, objectReferences, results )

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

# A lot more locations are stored in this file
with open( 'botw-tools/map_locations.js', 'r' ) as file :
    data = file.read().replace( 'var locations = ', '' ).rstrip().rstrip( ';' )
    global_map_locations = json.loads( data )

objectReferences = {}

# store things in a way where we can conveniently grab by "Hash"
# These "hashes" are not the same as the Save Data ones, so we will have to determine match-ups by the End X/Y Coordinates
for type in global_map_locations : 

    for hash in global_map_locations[ type ]['locations'] : 

        data = {
            "references": global_map_locations[ type ]["locations"][ hash ]['references'] if ( 'references' in global_map_locations[ type ]["locations"][ hash ] ) else [],
            "x": global_map_locations[ type ]["locations"][ hash ]['coords'][0],
            "y": global_map_locations[ type ]["locations"][ hash ]['coords'][1],
            "name": global_map_locations[ type ]["locations"][ hash ]['name'],
        }

        if ( global_map_locations[ type ]["locations"][ hash ]['name'] == 'Obj_Plant_Korok_A_01' ) :
            data["firstKorokFlower"] = global_map_locations[ type ]["locations"][ hash ]['firstKorokFlower']

        objectReferences[ hash ] = data

map_locations = open('map_locations.js','w')

map_locations.write('var korokPaths = {\n')

for hash in global_map_locations["FldObj_KorokGoal_A_01"]["locations"] : 

    # _01 removed from our ActorType to prevent oddities when checking against Korok Actors, since each Korok is an individual Actor and has an ID attached
    korokPath = findKorokPath( hash, ['FldObj_KorokStartingBlock_A', 'FldObj_KorokGoal_A'], objectReferences, {} )

    path = []
    points = []

    korokPath['path'].reverse()

    for pathItem in korokPath['path'] : 

        path.append( {
            "x": pathItem['x'],
            "y": pathItem['y'],
        } )

        img_x = int( pathItem['x']/2 + 3000 )
        img_y = int( pathItem['y']/2 + 2500 )

        points.append( (img_x, img_y) )

    map_locations.write( '"%s": {"points": %s},\n' % ( korokPath['korok'], json.dumps( path ) ) )

    map_draw.line( points, 'white', 3 )

for hash in global_map_locations["Obj_Plant_Korok_A_01"]["locations"] : 

    if ( global_map_locations["Obj_Plant_Korok_A_01"]["locations"][ hash ]["firstKorokFlower"] != 'true' ) :
        continue

    # _01 removed from our ActorType to prevent oddities when checking against Korok Actors, since each Korok is an individual Actor and has an ID attached
    korokPath = findKorokPath( hash, ['Obj_Plant_Korok_A'], objectReferences, {} )

    path = []
    points = []

    for pathItem in korokPath['path'] : 

        path.append( {
            "x": pathItem['x'],
            "y": pathItem['y'],
        } )

        img_x = int( pathItem['x']/2 + 3000 )
        img_y = int( pathItem['y']/2 + 2500 )

        points.append( (img_x, img_y) )

    map_locations.write( '"%s": {"points": %s},\n' % ( korokPath['korok'], json.dumps( path ) ) )

    map_draw.line( points, 'white', 3 )

map_locations.write('};\n')

tracked_locations = open('tracked_locations.txt')

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
            map_locations.write('%s: {"internal_name":"%s", "display_name":"%s", "x":%g, "y":%g},\n' % ( get_hash_from_internal_name( saveflag, gamedata ), saveflag, name, x, z ) )

            img_x = int(x/2 + 3000)
            img_y = int(z/2 + 2500)
            map_draw.ellipse((img_x-CIRCLE_RADIUS, img_y-CIRCLE_RADIUS, img_x+CIRCLE_RADIUS, img_y+CIRCLE_RADIUS), fill='orange', outline='red')

            found = True
            break
    if not found:
        print('Not found %s (%s)' % (location, name))

map_locations.write('};\n')

# Grabs Warps
warps = open('warps.txt')

map_locations.write('var warps = {\n')

for line in warps : 
    warp = line.strip()
    found = False
    name = None
    if warp in location_names:
        name = location_names[warp]
    for value in static_values:
        saveflag = value.findall('./SaveFlag')[0].text
        
        if 'Location_' + warp == saveflag:
            messageIDs = value.findall('./MessageID')
            if not name and len(messageIDs) and (messageIDs[0].text in location_names):
                name = location_names[messageIDs[0].text]
            if not name:
                name = warp
            
            translate = value.findall('./Translate')[0]
            x,y = float(translate.attrib['X'].rstrip('f')), float(translate.attrib['Z'].rstrip('f'))
            map_locations.write('%s: {"internal_name":"%s", "display_name":"%s", "x":%g, "y":%g},\n' % ( get_hash_from_internal_name( saveflag, gamedata ), saveflag, name, x, y ) )

            img_x = int(x/2 + 3000)
            img_y = int(y/2 + 2500)
            map_draw.polygon((img_x-CIRCLE_RADIUS,img_y,img_x,img_y-CIRCLE_RADIUS,img_x+CIRCLE_RADIUS,img_y,img_x,img_y+CIRCLE_RADIUS,img_x-CIRCLE_RADIUS,img_y),fill='cyan',outline='blue')

            found = True
            break
    if not found:
        print('Not found %s (%s)' % (warp, name))


map_locations.write('};\n')

tracked_locations.close()

# Grabs Koroks
static_values = ET.parse('Static.xml').getroot().findall('./*/value/Flag/..')

map_locations.write('var koroks = {\n')

for value in static_values:

    flag = value.findall('./Flag')[0].text
    translate = value.findall('./Translate')[0]
    x,y = float(translate.attrib['X'].rstrip('f')), float(translate.attrib['Z'].rstrip('f'))

    hash = get_hash_from_internal_name( flag, gamedata )

    map_locations.write('%s: {"internal_name":"%s", "display_name":"%s", "x":%g, "y":%g},\n' % ( hash, flag, 'Korok', x, y ) )

    img_x = int(x/2 + 3000)
    img_y = int(y/2 + 2500)
    map_draw.ellipse((img_x-CIRCLE_RADIUS, img_y-CIRCLE_RADIUS, img_x+CIRCLE_RADIUS, img_y+CIRCLE_RADIUS), fill='lime', outline='green')

map_locations.write('};\n')

map_locations.close()

botw_map.save('BotW-Map-Labeled.png')