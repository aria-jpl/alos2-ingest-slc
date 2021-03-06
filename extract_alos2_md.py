#!/usr/bin/env python3
import glob
import os
from subprocess import check_call, check_output
import pickle
import argparse
import datetime
import json
import re
import requests

#!/usr/bin/env python3
# David Bekaert - Jet Propulsion Laboratory
# set of functions that are leveraged in the packaging of the ARIA standard product 

from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
import glob
import os
import xml_json_converter

def loadProduct(xmlname):
    '''
    Load the product using Product Manager.
    '''
    # from Cunren's code on extracting track data from alos2App
    import isce, isceobj
    from iscesys.Component.ProductManager import ProductManager as PM

    print("loadProduct(xmlname) : {}".format(xmlname))
    pm = PM()
    pm.configure()
    obj = pm.loadProduct(xmlname)
    return obj


def loadTrack(date):
    '''
    date: YYMMDD
    '''
    # from Cunren's code on extracting track data from alos2App
    track = loadProduct('{}.track.xml'.format(date))
    track.frames = []
    frameParameterFiles = sorted(glob.glob(os.path.join('f*_*', '{}.frame.xml'.format(date))))
    for x in frameParameterFiles:
        track.frames.append(loadProduct(x))
    return track

def getTrackFrameData(track):
    '''
    get frame information 
    '''
    import datetime

    frameData = {}

    numberOfFrames = len(track.frames)
    numberOfSwaths = len(track.frames[0].swaths)

    rangePixelSizeList = []
    sensingStartList = []
    sensingEndList = []
    startingRangeList = []
    endingRangeList = []
    azimuthLineIntervalList =[]
    azimuthPixelSizeList = []
    swaths = []

    for i in range(numberOfFrames):
        for j in range(numberOfSwaths):
            swath = track.frames[i].swaths[j]
            swaths.append(swath)
            rangePixelSizeList.append(swath.rangePixelSize)
            azimuthLineIntervalList.append(swath.azimuthLineInterval)
            azimuthPixelSizeList.append(swath.azimuthPixelSize)
            sensingStartList.append(swath.sensingStart)
            sensingEndList.append(swath.sensingStart + datetime.timedelta(seconds=(swath.numberOfLines-1) * swath.azimuthLineInterval))
            startingRangeList.append(swath.startingRange)
            endingRangeList.append(swath.startingRange + (swath.numberOfSamples - 1) * swath.rangePixelSize)
    azimuthTimeMin = min(sensingStartList)
    azimuthTimeMax = max(sensingEndList)
    azimuthTimeMid = azimuthTimeMin+datetime.timedelta(seconds=(azimuthTimeMax-azimuthTimeMin).total_seconds()/2.0)
    rangeMin = min(startingRangeList)
    rangeMax = max(endingRangeList)
    rangeMid = (rangeMin + rangeMax) / 2.0

    bbox = [rangeMin, rangeMax, azimuthTimeMin, azimuthTimeMax]
    pointingDirection = {'right': -1, 'left': 1}
    
     #####################################
    # in image coordinate
    #         1      2
    #         --------
    #         |      |
    #         |      |
    #         |      |
    #         --------
    #         3      4
    # in geography coorindate
    #        1       2
    #         --------
    #         \       \
    #          \       \
    #           \       \
    #            --------
    #            3       4
    #####################################
    # in image coordinate

    # corner 1
    llh1 = track.orbit.rdr2geo(azimuthTimeMin, rangeMin, height=0, side=pointingDirection[track.pointingDirection])
    # corner 2
    llh2 = track.orbit.rdr2geo(azimuthTimeMin, rangeMax, height=0, side=pointingDirection[track.pointingDirection])
    # corner 3
    llh3 = track.orbit.rdr2geo(azimuthTimeMax, rangeMin, height=0, side=pointingDirection[track.pointingDirection])
    # corner 4
    llh4 = track.orbit.rdr2geo(azimuthTimeMax, rangeMax, height=0, side=pointingDirection[track.pointingDirection])

    # re-sort in geography coordinate
    if track.passDirection.lower() == 'descending':
        if track.pointingDirection.lower() == 'right':
            footprint = [llh2, llh1, llh4, llh3]
        else:
            footprint = [llh1, llh2, llh3, llh4]
    else:
        if track.pointingDirection.lower() == 'right':
            footprint = [llh4, llh3, llh2, llh1]
        else:
            footprint = [llh3, llh4, llh1, llh2]

    
    frameData['numberOfFrames'] = numberOfFrames
    frameData['numberOfSwaths'] = numberOfSwaths 
    frameData['rangePixelSizeList'] = rangePixelSizeList
    frameData['sensingStartList'] = sensingStartList
    frameData['sensingEndList'] = sensingEndList
    frameData['startingRangeList'] = startingRangeList
    frameData['endingRangeList'] = endingRangeList
    frameData['azimuthLineIntervalList'] = azimuthLineIntervalList
    frameData['azimuthPixelSizeList'] = azimuthPixelSizeList
    frameData['bbox'] = bbox
    frameData['footprint'] = footprint
    frameData['swaths'] = swaths
    frameData['rangeMin'] = rangeMin
    frameData['rangeMax'] = rangeMax
    frameData['rangeMid'] = rangeMid

    return frameData


def get_alos2_obj(dir_name):
    import os
    import glob
    import re
    from subprocess import check_call, check_output

    track = None
    img_file = sorted(glob.glob(os.path.join(dir_name, 'IMG*')))

    if len(img_file) > 0:
        match = re.search('IMG-[A-Z]{2}-(ALOS2)(.{05})(.{04})-(\d{6})-.{4}.*',img_file[0])
        if match:
            date = match.group(4)
            create_alos2app_xml(dir_name)
            check_output("alos2App.py --steps --end=preprocess", shell=True)
            track = loadTrack(date)
            track.spacecraftName = match.group(1)
            track.orbitNumber = match.group(2)
            track.frameNumber = match.group(3)

    return track

def get_alos2_bbox(args):
    import json

    ref_json_file = args[0]
    with open (ref_json_file, 'r') as f:
        data = json.load(f)

    return data['bbox']

    
def get_alos2_bbox_from_footprint(footprint):
    bbox = []
    for i in range(len(footprint)):
        bbox.append([footprint[i][0], footprint[i][1]])
    return bbox

def create_alos2_md_json(dirname):
    from scipy.constants import c
    from statistics import mean

    track = get_alos2_obj(dirname)
    frameData = getTrackFrameData(track)
    bbox = frameData['footprint']
    
    md = {}
    md['geometry'] = {
        "coordinates":[[
        bbox[0][1:None:-1], # NorthWest Corner
        bbox[1][1:None:-1], # NorthEast Corner
        bbox[3][1:None:-1], # SouthWest Corner
        bbox[2][1:None:-1], # SouthEast Corner
        bbox[0][1:None:-1],
        ]],
        "type":"Polygon"
    }
    md['sensing_start'] = "{}".format(min(frameData['sensingStartList']).strftime("%Y-%m-%dT%H:%M:%S.%f"))
    md['sensing_stop'] = "{}".format(max(frameData['sensingEndList']).strftime("%Y-%m-%dT%H:%M:%S.%f"))
    md['absolute_orbit'] = track.orbitNumber
    md['frame'] = track.frameNumber
    md['flight_direction'] = 'asc' if 'asc' in track.catalog['passdirection'] else 'dsc'
    md['satellite_name'] = track.spacecraftName
    md['source'] = "isce_preprocessing"
    md['bbox'] = get_alos2_bbox_from_footprint(bbox)
    md['pointing_direction'] = track.catalog['pointingdirection']
    md['radar_wave_length'] = track.catalog['radarwavelength']
    md['starting_range'] = min(frameData['startingRangeList'])
    md['azimuth_pixel_size'] = mean(frameData['azimuthPixelSizeList'])
    md['azimuth_line_interval'] = mean(frameData['azimuthLineIntervalList'])
    md['frequency'] = old_div(c, track.catalog['radarwavelength'])
    md['orbit_type'] = get_orbit_type(track.orbit.getOrbitQuality())
    md['orbit_source'] = track.orbit.getOrbitSource()
    md['nearRange'] = frameData['rangeMin']
    md['farRange'] = frameData['rangeMax']
    md['rangePixelSize'] = mean(frameData['rangePixelSizeList'])

    return md

def get_orbit_type(orbit_quality):
    if 'precision' in orbit_quality:
        return "POEORB"
    return "RESORB"

def create_alos2_md_file(dirname, filename):
    import json
    md = create_alos2_md_json(dirname)
    #print(md)
    with open(filename, "w") as f:
        json.dump(md, f, indent=2)
        f.close()


def get_alos2_metadata_variable(args):
    '''
        return the value of the requested variable
    '''

    data = None
    masterdir = args[0]
    variable = args[1]

    print("\n\nget_alos2_metadata_variable(args) : {}".format(args))

    alos2_metadata = get_alos2_metadata_reference_json(args[0]) #create_alos2_md_json(masterdir) # get_alos2_metadata(masterdir)
    if variable in alos2_metadata:
        data = alos2_metadata[variable]

    return data

def get_alos2_metadata_reference_json(ref_json_file):
    import json

    data = {}
    with open (ref_json_file, 'r') as f:
        data = json.load(f)
    return data



def create_alos2app_xml(dir_name):
    fp = open('alos2App.xml', 'w')
    fp.write('<alos2App>\n')
    fp.write('    <component name="alos2insar">\n')
    fp.write('        <property name="master directory">{}</property>\n'.format(os.path.abspath(dir_name)))
    fp.write('        <property name="slave directory">{}</property>\n'.format(os.path.abspath(dir_name)))
    fp.write('    </component>\n')
    fp.write('</alos2App>\n')
    fp.close()



def create_alos2_md_bos(dir_name, filename):
    img_file = sorted(glob.glob(os.path.join(dir_name, 'IMG*')))
    geo_server = "https://portal.bostechnologies.com/geoserver/bos/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=bos:sarcat&maxFeatures=50&outputFormat=json"
    if len(img_file) > 0:
        m = re.search('IMG-[A-Z]{2}-(ALOS2.{16})-.*', os.path.basename(img_file[0]))
        id = m.group(1)
        params = {'cql_filter': "(identifier='{}')".format(id)}

        r = requests.get(geo_server, params, verify=False)
        r.raise_for_status()

        md = r.json()["features"][0]
        md['source'] = "bos_sarcat"
        # move properties a level up
        md.update(md['properties'])
        del md['properties']
        with open(filename, "w") as f:
            json.dump(md, f, indent=2)
            f.close()

def cmdLineParse():
    '''
    Command line parser.
    '''
    parser = argparse.ArgumentParser( description='extract metadata from ALOS2 1.1 with ISCE')
    parser.add_argument('--dir', dest='alos2dir', type=str, default=".",
            help = 'directory containing the L1.1 ALOS2 CEOS files')
    parser.add_argument('--output', dest='op_json', type=str, default="alos2_md.json",
                        help='json file name to output metadata to')
    parser.add_argument('--method', dest='method', type=str, default="",
                        help='either "bos" (to get md from bos) or "isce" (to get md from isce preprocessing) or empty (to get from bos, fallback isce)')
    return parser.parse_args()

if __name__ == '__main__':
    args = cmdLineParse()
    if args.method == "bos":
        create_alos2_md_bos(args.alos2dir, args.op_json)
    elif args.method == "isce":
        insar_obj = get_alos2_obj(args.alos2dir)
        create_alos2_md_isce(insar_obj, args.op_json)
    else:
        try:
            create_alos2_md_bos(args.alos2dir, args.op_json)
        except Exception as e:
            print("Got exception trying to query bos sarcat: %s" % str(e))
            # use isce if we are unable to get the bbox from bos
            create_alos2_md_isce(args.alos2dir, args.op_json)






