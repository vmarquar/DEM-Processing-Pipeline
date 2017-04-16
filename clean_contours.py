#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created on 11.04.2017
# creates several contour sets of a tiled raster source that contains multiple rasters
# creates a smooth contour set

import gdal, glob, subprocess, os
from osgeo.gdalconst import *
from osgeo import ogr

# def delete_Feature(input_shp,feature_list):
#     driver = ogr.GetDriverByName("ESRI Shapefile")
#     dataSource = driver.Open(input_shp, 0)
#     layer = dataSource.GetLayer()
#
#      # Create the output LayerS
#     outShapefile = input_shp[:-4]+'_del.shp'
#     outDriver = ogr.GetDriverByName("ESRI Shapefile")
#
#     # Remove output shapefile if it already exists
#     if os.path.exists(outShapefile):
#         outDriver.DeleteDataSource(outShapefile)
#
#     # Create the output shapefile
#     outDataSource = outDriver.CreateDataSource(outShapefile)
#     out_lyr_name = os.path.splitext( os.path.split( outShapefile )[1] )[0]
#     outLayer = outDataSource.CreateLayer( out_lyr_name, geom_type=ogr.wkbMultiPolygon )
#
#     # Add input Layer Fields to the output Layer if it is the one we want
#     inLayerDefn = inLayer.GetLayerDefn()
#     for i in range(0, inLayerDefn.GetFieldCount()):
#         fieldDefn = inLayerDefn.GetFieldDefn(i)
#         fieldName = fieldDefn.GetName()
#         if fieldName not in field_name_target:
#             continue
#         outLayer.CreateField(fieldDefn)
#
#     # Get the output Layer's Feature Definition
#     outLayerDefn = outLayer.GetLayerDefn()
#
#     # Add features to the ouput Layer
#     for inFeature in inLayer:
#         # Create output Feature
#         outFeature = ogr.Feature(outLayerDefn)
#
#         # Add field values from input Layer
#         for i in range(0, outLayerDefn.GetFieldCount()):
#             fieldDefn = outLayerDefn.GetFieldDefn(i)
#             fieldName = fieldDefn.GetName()
#             if fieldName not in field_name_target:
#                 continue
#
#             outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(),
#                 inFeature.GetField(i))

def join_lines(input_shp,input2_shp="DEFAULT",buffer_size=1000):
    '''
    input_shp and input2_shp: input shape files, may come from NSEW_Neighbourhood function
    '''
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(input_shp, 1)
    layer = dataSource.GetLayer()

    driver2 = ogr.GetDriverByName("ESRI Shapefile")
    dataSource2 = driver2.Open(input2_shp, 1)
    layer2 = dataSource2.GetLayer()

    for feature in layer:
        geom = feature.GetGeometryRef()
        first_vertice = geom.GetPoint(0)
        last_vertice = geom.GetPoint(geom.GetPointCount() - 1)

        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(first_vertice[0], first_vertice[1],first_vertice[2])
        # filter layer with buffer
        spatial_selection = layer.SetSpatialFilter(point.Buffer(buffer_size))
        spatial_selection2 = layer2.SetSpatialFilter(point.Buffer(buffer_size))

        print "First Vertice is {}. Last Vertice {}.".format(first_vertice,last_vertice)
        print "Found {} features in layer after spatial selection".format(layer.GetFeatureCount())
        print "Found {} features in layer2 after spatial selection".format(layer2.GetFeatureCount())
        for feature in spatial_selection:
            for feature2 in spatial_selection2:
                print feature.GetGeometryRef().Distance(feature2.GetGeometryRef())

shps = ['/Users/Valentin/Documents/GIS-Daten/DEM-Processing-Pipeline/data/export_3_1.shp','/Users/Valentin/Documents/GIS-Daten/DEM-Processing-Pipeline/data/export_10_1.shp']
join_lines(shps[0],shps[1],buffer_size=1000)



input_shp = shps[0]
input2_shp = shps[1]


def getLength(feature):
    # wkt = "LINESTRING (1181866.263593049 615654.4222507705, 1205917.1207499576 623979.7189589312, 1227192.8790041457 643405.4112779726, 1224880.2965852122 665143.6860159477)"
    # geom = ogr.CreateGeometryFromWkt(wkt)
    return feature.geometry().Length()
    print "Length = %d" % feature.geometry().Length()

def clean_features(input_shp, max_len=float('inf'), min_len=-1):
    """
    Removes Duplicates (features that have identical geomeotries) and filters features by their length.
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(input_shp, 1)
    layer = dataSource.GetLayer()
    geometries = []
    for feature in layer:
        geom = feature.GetGeometryRef()
        if (geom in geometries) or (feature.geometry().Length() > max_len) or (feature.geometry().Length() < min_len):
            # todo: delete feature
            print "Deleting Feature: ",feature.GetField("ID")
            # TODO: getFID() or GetField("ID") verbessern -> sehr fehleranfaellig
            # layer.DeleteFeature(feature.getFID())

            # TODO: ANSATZ WENN GEOM RD. 0.8 BIS 1.2 BETRÄGT DANN LÖSCHEN
            # TODO: WIE IST GEOM AUFGEBAUT? MIT KOORDINATEN

            layer.DeleteFeature(feature.GetField("ID"))
        else:
            geometries.append(geom)
    dataSource = None
    del dataSource

def delete_with_thresh(input_shp,src_bounds,other_bounds,neighbourhood_thresh, negative_buffer_in_m,max_len=float('inf'),min_len=-1):
    """
    Create Selection slices for each side of the raster where it has a neighbour.
    input_shp: path of input shapefile
    src_bounds: src bounds of raster
    other_bounds: raster where a Neighbourhood should be tested
    neighbourhood_thresh: distance in [m] where a Neighbourhood should apply
    negative_buffer_in_m: slice thickness from outer boundy of input raster to the inside
    """
    ll = src_bounds[0]
    lr = src_bounds[1]
    ur = src_bounds[2]
    ul = src_bounds[3]
    # returns a list of neighbours -> [['N',raster1],'S','raster2'...]
    neighbours = NSEW_Neighbourhood(src_bounds,other_bounds,neighbourhood_thresh)
    for direction in neighbours:

        slice_ftr = ogr.Geometry(ogr.wkbLinearRing)
        if direction[0] == 'N':
            slice_ftr.AddPoint(ul[0],ul[1])
            slice_ftr.AddPoint(ur[0],ur[1])
            slice_ftr.AddPoint(ur[0],ur[1]-negative_buffer_in_m)
            slice_ftr.AddPoint(ul[0],ul[1]-negative_buffer_in_m)

        if direction[0] == 'S':
            slice_ftr.AddPoint(ll[0],ll[1])
            slice_ftr.AddPoint(lr[0],lr[1])
            slice_ftr.AddPoint(lr[0],lr[1]+negative_buffer_in_m)
            slice_ftr.AddPoint(ll[0],ll[1]+negative_buffer_in_m)

        if direction[0] == 'E':
            slice_ftr.AddPoint(lr[0],lr[1])
            slice_ftr.AddPoint(ur[0],ur[1])
            slice_ftr.AddPoint(ur[0],ur[1]-negative_buffer_in_m)
            slice_ftr.AddPoint(lr[0],lr[1]-negative_buffer_in_m)
        if direction[0] == 'W':
            slice_ftr.AddPoint(ll[0],ll[1])
            slice_ftr.AddPoint(ul[0],ul[1])
            slice_ftr.AddPoint(ul[0],ul[1]+negative_buffer_in_m)
            slice_ftr.AddPoint(ll[0],ll[1]+negative_buffer_in_m)

        # Create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(slice_ftr)
        wkt = poly.ExportToWkt()
    try:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(input_shp, 1)
        layer = dataSource.GetLayer()
        layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))
        print wkt
        try:
            for feature in layer:
                if (feature.geometry().Length() < max_len) and (feature.geometry().Length() > min_len):
                    print "Deleting Feature: ",feature.GetField("ID")
                    # TODO: getFID() or GetField("ID") verbessern -> sehr fehleranfällig
                    # layer.DeleteFeature(feature.getFID())
                    layer.DeleteFeature(feature.GetField("ID"))
            pass
        except Exception as e:
            print "Error in selecting features. Maybe already selected?"
            dataSource = None
            del dataSource
            pass

        dataSource = None
        del dataSource
        pass
    except Exception as e:
        print "wkt probably does not exist."
        pass

def copy_with_thresh(input_shp,copy_shp,src_bounds,other_bounds,neighbourhood_thresh, negative_buffer_in_m,max_len=float('inf'),min_len=-1):
    """
    Create Selection slices for each side of the raster where it has a neighbour.
    input_shp: path of input shapefile
    copy_shp: source layer where features should be copied to
    src_bounds: src bounds of raster
    other_bounds: raster where a Neighbourhood should be tested
    neighbourhood_thresh: distance in [m] where a Neighbourhood should apply
    negative_buffer_in_m: slice thickness from outer boundy of input raster to the inside
    """
    ll = src_bounds[0]
    lr = src_bounds[1]
    ur = src_bounds[2]
    ul = src_bounds[3]
    # returns a list of neighbours -> [['N',raster1],'S','raster2'...]
    neighbours = NSEW_Neighbourhood(src_bounds,other_bounds,neighbourhood_thresh)
    for direction in neighbours:

        slice_ftr = ogr.Geometry(ogr.wkbLinearRing)
        if direction[0] == 'N':
            slice_ftr.AddPoint(ul[0],ul[1])
            slice_ftr.AddPoint(ur[0],ur[1])
            slice_ftr.AddPoint(ur[0],ur[1]-negative_buffer_in_m)
            slice_ftr.AddPoint(ul[0],ul[1]-negative_buffer_in_m)

        if direction[0] == 'S':
            slice_ftr.AddPoint(ll[0],ll[1])
            slice_ftr.AddPoint(lr[0],lr[1])
            slice_ftr.AddPoint(lr[0],lr[1]+negative_buffer_in_m)
            slice_ftr.AddPoint(ll[0],ll[1]+negative_buffer_in_m)

        if direction[0] == 'E':
            slice_ftr.AddPoint(lr[0],lr[1])
            slice_ftr.AddPoint(ur[0],ur[1])
            slice_ftr.AddPoint(ur[0],ur[1]-negative_buffer_in_m)
            slice_ftr.AddPoint(lr[0],lr[1]-negative_buffer_in_m)
        if direction[0] == 'W':
            slice_ftr.AddPoint(ll[0],ll[1])
            slice_ftr.AddPoint(ul[0],ul[1])
            slice_ftr.AddPoint(ul[0],ul[1]+negative_buffer_in_m)
            slice_ftr.AddPoint(ll[0],ll[1]+negative_buffer_in_m)

        # Create polygon
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(slice_ftr)
        wkt = poly.ExportToWkt()
    try:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(input_shp, 1)
        layer = dataSource.GetLayer()
        layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))
        # TODO: open output shape file layer
        #Create the output LayerS
        outDriver = ogr.GetDriverByName("ESRI Shapefile")
        copyDS = outDriver.Open(copy_shp, 1)
        layer_copy = copyDS.GetLayer()
        #TODO: create new attribute fiels if they do not exist in copy_shp

        try:
            for feature in layer:
                if (feature.geometry().Length() < max_len) and (feature.geometry().Length() > min_len):
                    print "Copying Feature: ",feature.GetField("ID")
                    # TODO copy features to new dataset
                    layer_copy.CreateFeature(feature)
            pass
        except Exception as e:
            print "Error in selecting features. Maybe already selected?"
            dataSource = None
            copyDS = None
            del dataSource
            del copyDS
            pass

        dataSource = None
        copyDS = None
        del copyDS
        del dataSource
        pass
    except Exception as e:
        print "wkt probably does not exist."
        pass

def create_raster_ring(input_path,src_bounds,negative_buffer_in_m,overwrite=False):
    """
    adapted from: https://pcjericks.github.io/py-gdalogr-cookbook/geometry.html
    input_path: Raster where a hole should be cut into
    negative_buffer_in_m: is the distance in m from the outside to the inner side
    src_bounds: [[ll],[lr],[ur],[ul]]
    Dependency: create_wkt_ring()
    """
    if os.path.isfile(input_path[:-4]+'_crop.tif') and overwrite != True:
        print "\n Cropped Raster file already exist: {} \nProceeding with next file without checking for varying parameters (e.g. buffer size).\n Force overwrite with overwrite=True...".format(input_path[:-4]+'_crop.tif')
        return None
    wkt_ring = create_wkt_ring(src_bounds,negative_buffer_in_m)
    f = open(os.path.join(os.path.dirname(input_path),'tmp.csv'), 'w')
    csv = 'id,WKT\n1,\"'+wkt_ring+'\"'
    f.write(csv)
    f.close()
    #TODO Clip the raster by the calculated Geometry
    # http://pcjericks.github.io/py-gdalogr-cookbook/layers.html#filter-and-select-input-shapefile-to-new-output-shapefile-like-ogr2ogr-cli
    cmd = ['gdalwarp', '-cutline', os.path.join(os.path.dirname(input_path),'tmp.csv'), '-crop_to_cutline', input_path, input_path[:-4]+'_crop.tif']
    try:
        subprocess.check_call(cmd)
        os.remove(os.path.join(os.path.dirname(input_path),'tmp.csv'))
        pass
    except Exception as e:
        print "could not gdalwarp with following cmd:\n\n",cmd
        print "\n\nDOES THE FILE ALREADY EXIST?\n\n"
        raise

def create_wkt_ring(src_bounds,negative_buffer_in_m):
    """
    creates a ring with outside coordinates from src_bounds and a negative buffer
    src_bounds: [[ll],[lr],[ur],[ul]]
    negative_buffer_in_m: distance that should be used to build the ring
    returns: WKT Polygon
    """
    ll = src_bounds[0]
    lr = src_bounds[1]
    ur = src_bounds[2]
    ul = src_bounds[3]
    # Create outer ring
    outRing = ogr.Geometry(ogr.wkbLinearRing)
    outRing.AddPoint(ll[0],ll[1])
    outRing.AddPoint(lr[0],lr[1])
    outRing.AddPoint(ur[0],ur[1])
    outRing.AddPoint(ul[0],ul[1])

    # Create inner ring
    innerRing = ogr.Geometry(ogr.wkbLinearRing)
    innerRing.AddPoint(ll[0]+negative_buffer_in_m,ll[1]+negative_buffer_in_m)
    innerRing.AddPoint(lr[0]-negative_buffer_in_m,lr[1]+negative_buffer_in_m)
    innerRing.AddPoint(ur[0]-negative_buffer_in_m,ur[1]-negative_buffer_in_m)
    innerRing.AddPoint(ul[0]+negative_buffer_in_m,ul[1]-negative_buffer_in_m)

    # Create polygon
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(outRing)
    poly.AddGeometry(innerRing)
    #TODO Export to shapefile
    #ogr.CreateGeometryFromWkt(wkt)
    return poly.ExportToWkt()
    print "Created Ring with buffer distance: ",negative_buffer_in_m

def create_vrt(input_rasters,outpath="DEFAULT",no_data_value=None,overwrite=False):
    """
    this function takes all negative buffered rasters
    and merges them into a raster hole like mosaic.
    This is necessary to obtain smooth contours where 4 rasters join together.
    input_crops: list of cropped rasters that should be merged as a vrt
    outpath: DEFAULT, takes the basepath of the first raster in input_rasters
    """


    cmd = ['gdalbuildvrt']
    if no_data_value != None:
        cmd.append('-srcnodata')
        cmd.append(str(no_data_value))
    if outpath == "DEFAULT":
        outpath = os.path.join(os.path.dirname(input_rasters[0]),'merged_rasters.vrt')
        cmd.append(outpath)
    else:
        outpath = os.path.join(outpath,'out.vrt')
        cmd.append(outpath)

    if os.path.isfile(outpath) and overwrite != True:
        print "\n Virtual Raster file already exist: {} \nProceeding with next step without checking for varying parameters (e.g. different input rasters).\n Force overwrite with overwrite=True...".format(outpath)
        return outpath

    #cmd.append(' '.join(input_rasters))
    cmd = cmd + input_rasters
    print cmd
    try:
        subprocess.check_call(cmd)
        # return path of newly created vrt
        return outpath
        pass
    except Exception as e:
        print "could not build virtual raster with following cmd:\n\n",cmd
        raise

def create_contours(input_path, spacing, shp_path="DEFAULT", contour_base=0, no_data=1,no_data_value=0,overwrite=False):
    """
    adapted from: http://stackoverflow.com/questions/22100453/gdal-python-creating-contourlines
    """
    if shp_path == "DEFAULT":
        shp_path = input_path[:-4]+'_contour.shp'
    if os.path.isfile(shp_path) and overwrite != True:
        print "\n Contour lines already exist: {} \nProceeding with next file without checking for varying parameters (e.g. contour line spacing).\n Force overwrite with overwrite=True...".format(shp_path)
        return shp_path
    try:
        #Read in SRTM data
        raster = gdal.Open( input_path, GA_ReadOnly)
        raster_band1 = raster.GetRasterBand(1)

        #Generate layer to save Contourlines in
        contour_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shp_path)
        contour_shp = contour_ds.CreateLayer('contour')

        field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
        contour_shp.CreateField(field_defn)
        field_defn = ogr.FieldDefn("height", ogr.OFTReal)
        contour_shp.CreateField(field_defn)
        #TODO create nth field here

        #Generate Contourlines
        # gdal.ContourGenerate(raster_band1,spacing,contourbase,fixedlevelcount,boleanusenodata,dfnodatavalue,hLayer,idField,iElevfield,progress,pProgressArg
        # http://www.gdal.org/gdal__alg_8h.html#aceaf98ad40f159cbfb626988c054c085
        gdal.ContourGenerate(raster_band1, spacing, contour_base, [], no_data, no_data_value, contour_shp, 0, 1)
        # TODO: delete small features < 1000m
        # more info here: http://pcjericks.github.io/py-gdalogr-cookbook/layers.html#filter-and-select-input-shapefile-to-new-output-shapefile-like-ogr2ogr-cli
        contour_ds = None
        del contour_ds
        return shp_path
        pass
    except Exception as e:
        print "createContours() could not finish it's duty Sir!"
        raise

def get_bounds(input_path):
    """
    gets bounding corners of a raster (approximated as a square)
    counterclockwise from llx,lly -> lrx,lry -> urx,ury -> ulx,uly
    """
    src = gdal.Open(input_path)
    ulx, xres, xskew, uly, yskew, yres = src.GetGeoTransform()
    lrx = ulx + (src.RasterXSize * xres)
    lry = uly + (src.RasterYSize * yres)

    # can be deleted and replaced by line 21 after dev phase
    ll = [ulx,lry] # lower left
    lr = [lrx,lry] # lower right
    ur = [lrx,uly] # upper right
    ul = [ulx,uly] # upper left
    return [ll,lr,ur,ul]
    #return [[ulx,lry],[lrx,lry],[lrx,lry],[ulx,uly]]

def NSEW_Neighbourhood(src_bounds,other_bounds,thresh):
    """
    checks the N,S,E,W Neighbourhood for raster tiles
    src_bounds: list obtained from get_bounds of the source raster
    other_bounds: dict of all other raster boundaries {raster_name: [list of bounds]}
    get mean point of each direction and add threshhold
    returns: [[direction, raster path], [direction, raster path], ...]
    """
    mean_N = [((src_bounds[2][0]+src_bounds[3][0])/2), (((src_bounds[2][1]+src_bounds[3][1])/2)+thresh)]
    mean_S = [((src_bounds[0][0]+src_bounds[1][0])/2), (((src_bounds[0][1]+src_bounds[1][1])/2)-thresh)]
    mean_E = [(((src_bounds[1][0]+src_bounds[2][0])/2)+thresh), ((src_bounds[1][1]+src_bounds[2][1])/2)]
    mean_W = [(((src_bounds[0][0]+src_bounds[3][0])/2)-thresh), ((src_bounds[0][1]+src_bounds[3][1])/2)]

    neighbours = []
    for raster, bounds in other_bounds.iteritems():
        ll,lr,ur,ul = bounds
        # check if mean points are in a bounding box of a other raster
        # assumes a rectangle raster file aligned to x,y axis
        directions = {'N':mean_N,'S':mean_S,'E':mean_E,'W':mean_W}

        # TODO TODO FEHLER IN DER LOGISCHEN ABFRAGE -> KEIN ERGEBNIS
        for direction, point in directions.iteritems(): # TOCHECK TODO
            #print direction, point, [ll,lr,ur,ul]
            # xmin < xtest < xmax and ymin < ytest < ymax
            if (point[0] >= ll[0] and point[0] <= ur[0]) and (point[1] >= ll[1] and point[1] <= ur[1]):
                print "located: "+raster+' in the '+direction
                neighbours.append([direction,raster])

        # TODO Exit bei vier rastern!
        if len(neighbours) > 3:
            return neighbours
            # returns a list of neighbours -> [['N',raster1],'S','raster2'...]

    return neighbours
# directory must be provided with a trailing slash e.g. my/dir/
def get_tifs(directory):
    tifs10_99 =  glob.glob(directory+'[0-9][0-9].tif')
    tifs0_9 =  glob.glob(directory+'[0-9].tif')
    return (tifs0_9+tifs10_99)


# TESTING

#Test tifs
#tifs = ['/Volumes/TOSHIBA EXT/EU-DEM/tiles/10.tif']
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/11.tif',
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/17.tif',
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/16.tif',
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/2.tif',
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/3.tif',
# '/Volumes/TOSHIBA EXT/EU-DEM/tiles/9.tif']
# #create_contours(tifs[0], 50, shp_path="DEFAULT", contour_base=0, no_data=1,no_data_value=0)
# #
# all_bounds = {}
# for tif in tifs:
#     all_bounds[tif] = get_bounds(tif)
# #print all_bounds
# src_bounds = all_bounds['/Volumes/TOSHIBA EXT/EU-DEM/tiles/1.tif']
# # print NSEW_Neighbourhood(src_bounds,all_bounds,7500)

#print src_bounds
# 10 km cutline
#create_raster_ring('/Volumes/TOSHIBA EXT/EU-DEM/tiles/1.tif',src_bounds,10000)
#create_vrt(['/Volumes/TOSHIBA EXT/EU-DEM/tiles/1.tif','/Volumes/TOSHIBA EXT/EU-DEM/tiles/10.tif'],outpath="DEFAULT",no_data_value=0)

# if __name__ == '__main__':
#     tifs = get_tifs('/Volumes/TOSHIBA EXT/EU-DEM/tiles/')
#     all_bounds = {}
#     for tif in tifs:
#         all_bounds[tif] = get_bounds(tif)
#
#     # 1. Create contour lines for each raster tile
#     tile_contours = []
#     for tif in tifs:
#         # creates a 10 m spaced contour line dataset with a default file ending of *_contour.shp
#         tile_contours.append(create_contours(tif, 10, shp_path="DEFAULT", contour_base=0, no_data=1,no_data_value=0))
#
#     # 2.1 Create new raster buffer zone (cut holes in each tile and merge them together to a vrt)
#     # 2.2 Create a seemless vrt raster file from all tiles
#     input_rasters = []
#     for tif in tifs:
#         src_bounds = all_bounds[tif]
#         create_raster_ring(tif,src_bounds,5000)
#         input_rasters.append(tif[:-4]+'_crop.tif')
#     vrt = create_vrt(input_rasters,outpath="DEFAULT",no_data_value=0)
#
#     # 3. Calculate contours in new buffer zone
#     # creates new contour ds in buffered zone and returns the path of the new file
#     buffer_contours = create_contours(vrt, 10, shp_path="DEFAULT", contour_base=0, no_data=1,no_data_value=0)
#
#     # 4. Delete all edge contour lines from tile_contours (which where created at step 1)
#     for tif in tifs:
#         # DEFAULT CASE:
#         contour_shp = tif[:-4]+'_contour.shp'
#         src_bounds = all_bounds[tif]
#         other_bounds = {i:all_bounds[i] for i in all_bounds if i!=tif}
#         print '\n',other_bounds
#         #raw_input("Press a key to continue...")
#         delete_with_thresh(contour_shp ,src_bounds,other_bounds,5000, 500,max_len=5000)
#
#     # 5. Take all contours from buffered contours and copy them into their tile contour partner
#     for tif in tifs:
#         input_shp = buffer_contours
#         src_bounds = all_bounds[tif]
#         other_bounds = {i:all_bounds[i] for i in all_bounds if i!=tif}
#         # TODO: copy_shp = "DEFAULT"
#         # TODO: define copy_shp -> Die Features welche
#         # ACHTUNG VEREINFACHUNG! Danach müssen die Shapefiles auf duplicate überprüft werden!!!
#         copy_shp = tif[:-4]+'_contour.shp'
#         copy_with_thresh(input_shp,copy_shp,src_bounds,other_bounds,5000, 100,max_len=float('inf'),min_len=1000)
#
#     # 6. Clean contour datasets by removing identical features and filter small features with a minimum length of 1000 m
#     for tile_contour in tile_contours:
#         clean_features(input_shp, max_len=float('inf'), min_len=1000)
