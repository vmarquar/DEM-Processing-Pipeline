#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Created on 11.04.2017
# creates several contour sets of a tiled raster source that contains multiple rasters
# creates a smooth contour set

import gdal, glob, subprocess, os
from osgeo.gdalconst import *
from osgeo import ogr

# TODO: enable first point joining (or check if its needed!)
def join_lines(buffer_size,input_shp,input2_shp="DEFAULT"):

    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(input_shp, 1)
    layer = dataSource.GetLayer()
    print "Found {} features in layer ".format(layer.GetFeatureCount())
    # ext = layer.GetExtent()
    # SetSpatialFilterRect(ext[0],ext[1],ext[2],ext[3])

    if input2_shp != "DEFAULT":
        driver2 = ogr.GetDriverByName("ESRI Shapefile")
        dataSource2 = driver2.Open(input2_shp, 1)
        layer2 = dataSource2.GetLayer()
        print "Found {} features in layer2 ".format(layer2.GetFeatureCount())
        # ext2 = layer2.GetExtent()
        layers = [layer,layer2]
    else:
        layers = [layer]

    # Collect all first vertices and last vertices from input layer(s)
    all_points = []

    for layer in layers:

        for feature in layer:
            try:
                print "feature {}".format(feature.GetField("ID"))
                print "layer: {}".format(layer.GetName())
                first_geom = feature.geometry()
                first_vertice = first_geom.GetPoint(0)
                vertice_number = len(feature.GetGeometryRef().GetPoints())
                last_vertice = feature.GetGeometryRef().GetPoint((vertice_number-1))
                print "ID: {}; FIRST: {}; LAST: {}".format(feature.GetField("ID"),first_vertice,last_vertice)

                first_point = ogr.Geometry(ogr.wkbPoint)
                first_point.AddPoint(first_vertice[0], first_vertice[1],first_vertice[2])
                last_point = ogr.Geometry(ogr.wkbPoint)
                last_point.AddPoint(last_vertice[0], last_vertice[1],last_vertice[2])

                add_point = {"ID":feature.GetField("ID"), "geometry":first_point, "position":'first', "layer":layer, "feature": feature}
                all_points.append(add_point)
                add_point = {"ID":feature.GetField("ID"), "geometry":last_point, "position":'last', "layer":layer, "feature": feature}
                all_points.append(add_point)
                pass
            except Exception as e:
                print e
                pass


        #print "First VERTICES: {} \n\n Last VERTICES: {}".format(first_vertices,last_vertices)
        print "\n All Points: {}".format(all_points)
        # first_geom = all_points[0]["geometry"]
        # last_geom = all_points[-1]["geometry"]

        #print "first x {} first y {} first z {} layer {} ID {}".format(first_geom.GetX(), first_geom.GetY(),first_geom.GetZ(),all_points[0]["layer"].GetName(),all_points[0]["ID"])
        #print "last x {} last y {} last z {} layer {} ID {}".format(last_geom.GetX(), last_geom.GetY(),last_geom.GetZ(),all_points[-1]["layer"].GetName(), all_points[-1]["ID"])
        # all_points = {"ID":int, "geometry": ogr.Geometry(ogr.wkbPoint), "position": 'first' or 'last', "layer": '/path/to/layer/shp'}
        #print "x: {} y: {} z: {} ID: {} layer: {} Length: {}".format(point["geometry"].GetX(),point["geometry"].GetY(),point["geometry"].GetZ(),point["layer"].GetName(),point["geometry"].Length())

        for point in all_points:

            #1. Buffer around point
            point_buffer = point["geometry"].Buffer(buffer_size)

            #[1.1] Spatial selection with buffer

            #2. Get closest point in buffer area, check for same height

            # filter out points with (a) the same ID (b) points with a different z-attribute (c) points that are outside the buffer distance)
            other_points = list(filter(lambda x: x["ID"]!= point["ID"] and (x["feature"].GetField("height") == point["feature"].GetField("height")) and point_buffer.Contains(x["geometry"]), all_points))
            smallest_distance = {"distance":float('inf'),"point":''}
            for other in other_points:
                print point["geometry"].Distance(other["geometry"])
                if point["geometry"].Distance(other["geometry"]) < smallest_distance["distance"]:
                    smallest_distance["distance"] = point["geometry"].Distance(other["geometry"])
                    smallest_distance["point"] = other
                    #print "x: {} y: {} z: {} ID: {} layer: {} Length:".format(point["geometry"].GetX(),point["geometry"].GetY(),point["geometry"].GetZ(),point["ID"],point["layer"].GetName())
                    #print "x: {} y: {} z: {} ID: {} layer: {} Length:".format(other["geometry"].GetX(),other["geometry"].GetY(),other["geometry"].GetZ(),other["ID"],other["layer"].GetName())
            print "smallest distance in from point was: {} and name was {}".format(smallest_distance['distance'],smallest_distance['point'])

            #3. Add new start / end point @ closest point location if criteria above are True
            if smallest_distance["distance"] != float('inf') and point["position"]=="last":
                try:
                    print "smallest distance in from point was: {} and name was {}".format(smallest_distance['distance'],smallest_distance['point'])

                    # Jetziger Status: smallest_distance liefert die distanz und das punkt objekt welches addPoint() bestimmt
                    # TODO: über punkt objekt den jeweiligen layer öffnen > das jeweilige feature öffnen und dort einen neuen punkt hinzufügen
                    # über terminal ausprobieren 1 shapelinie > addPoint > wird gleich geschrieben?
                    #layer_definition = point["layer"].GetLayerDefn()

                    # Get the input Feature
                    inFeature = point["feature"]
                    print "old geometry Length is: {}".format(inFeature.geometry().Length())
                    # Create output Feature
                    #outFeature = ogr.Feature(outLayerDefn)
                    # Add field values from input Layer
                    #for i in range(0, outLayerDefn.GetFieldCount()):
                    #    outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
                    # Set geometry as centroid
                    new_x = smallest_distance["point"]["geometry"].GetX()
                    new_y = smallest_distance["point"]["geometry"].GetY()
                    new_z = smallest_distance["point"]["geometry"].GetZ()

                    # geom = inFeature.geometry()
                    # print "geom is: {}".format(geom)
                    print "Addind new point at X: {} , Y: {}, Z: {}".format(new_x,new_y,new_z)
                    # new_geom = geom.AddPoint(smallest_distance["point"]["geometry"].GetX(),smallest_distance["point"]["geometry"].GetY(),smallest_distance["point"]["geometry"].GetZ())
                    # print "new_geom is: {}".format(new_geom)
                    inFeature.geometry().AddPoint(new_x,new_y,new_z)
                    print "added point successfully. "
                    #outFeature.SetGeometry(new_geom)
                    # delete geom
                    # set new geom
                    # MACHT PROBLEME!
                    #inFeature.SetGeometry(inFeature.geometry())
                    print "new geometry Length is: {}".format(inFeature.geometry().Length())
                    # Add new feature to output Layer
                    point["layer"].SetFeature(inFeature)
                    # inFeature = None

                    pass
                except Exception as e:
                    print e
                    pass


    # write data to disk
    if input2_shp != "DEFAULT":
        dataSource2 = None
        del dataSource2
    dataSource = None
    del dataSource

def get_shps(directory):
    """
    provide directory with a trailing slash, e.g. path/to/my/dir/
    """
    #shps10_99 =  glob.glob(directory+'[0-9][0-9].shp')
    #shps0_9 =  glob.glob(directory+'[0-9].shp')
    #return (tifs0_9+tifs10_99)
    return glob.glob(directory+'*.shp')

def get_shp_bounds(input_shp):
    """
    gets minimum bounding rectangle (mbr)
    counterclockwise from llx,lly -> lrx,lry -> urx,ury -> ulx,uly
    """
    try:
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(input_shp, 0)
        layer = dataSource.GetLayer()

        minx, maxx, miny, maxy = layer.GetExtent() # (1227841.2311797712, 1253712.155662728, 6101830.197181817, 6115091.489706456) > bounds for test1.shp

        ll = [minx,miny] # lower left
        lr = [maxx,miny] # lower right
        ur = [maxx,maxy] # upper right
        ul = [minx,maxy] # upper left
        return [ll,lr,ur,ul]

    except Exception as e:
        print "Could not compute bounding box. Reasons may be that there are no geometries in the layer, the bounding box isnt precomputed etc.\n"
        print "Following error occured: {}".format(e)

def NSEW_Neighbourhood(src_bounds,other_bounds,thresh):
    """
    checks the N,S,E,W Neighbourhood for tiles
    src_bounds: list obtained from get_bounds of the source vector_layer
    other_bounds: dict of all other raster boundaries {vector_name: [list of bounds]}
    get mean point of each direction and add threshhold
    returns: [[direction, vector path], [direction, vector path], ...]
    """
    mean_N = [((src_bounds[2][0]+src_bounds[3][0])/2), (((src_bounds[2][1]+src_bounds[3][1])/2)+thresh)]
    mean_S = [((src_bounds[0][0]+src_bounds[1][0])/2), (((src_bounds[0][1]+src_bounds[1][1])/2)-thresh)]
    mean_E = [(((src_bounds[1][0]+src_bounds[2][0])/2)+thresh), ((src_bounds[1][1]+src_bounds[2][1])/2)]
    mean_W = [(((src_bounds[0][0]+src_bounds[3][0])/2)-thresh), ((src_bounds[0][1]+src_bounds[3][1])/2)]

    neighbours = []
    for vector_layer, bounds in other_bounds.iteritems():
        ll,lr,ur,ul = bounds
        # check if mean points are in a bounding box of a other vector_layer
        # assumes a rectangle vector_layer file aligned to x,y axis
        directions = {'N':mean_N,'S':mean_S,'E':mean_E,'W':mean_W}

        # TODO TODO FEHLER IN DER LOGISCHEN ABFRAGE -> KEIN ERGEBNIS
        for direction, point in directions.iteritems(): # TOCHECK TODO
            #print direction, point, [ll,lr,ur,ul]
            # xmin < xtest < xmax and ymin < ytest < ymax
            if (point[0] >= ll[0] and point[0] <= ur[0]) and (point[1] >= ll[1] and point[1] <= ur[1]):
                print "located: "+vector_layer+' in the '+direction
                neighbours.append([direction,vector_layer])

        # TODO Exit bei vier rastern!
        if len(neighbours) > 3:
            return neighbours
            # returns a list of neighbours -> [['N',raster1],'S','raster2'...]

    return neighbours

#join_lines(buffer_size,input_shp, input2_shp)

# Variables:
shp_path = '/Volumes/TOSHIBA EXT/test-contours/'
buffer_size = 50 #50 - 100 [m], depends on slope
neighbourhood_thresh = 500 #[m]



if __name__ == '__main__':
    shps = get_shps(shp_path)
    all_bounds = {}
    neighbours = {} # {'src_shape','neighbour_list'}
    for shp in shps:
        # compute mbr's for all shapefiles
        all_bounds[shp] = get_shp_bounds(shp)



        # Compute neighbours
        src_bounds = all_bounds[shp]
        other_bounds = {i:all_bounds[i] for i in all_bounds if i!=shp}
        #print "src_bounds {}. other_bounds {}".format(src_bounds,other_bounds)
        neighbours[shp] = NSEW_Neighbourhood(src_bounds,other_bounds,neighbourhood_thresh)

        # Connect shapelines
        for neighbour in neighbours[shp]:
            if neighbour != []:
                direction = neighbour[0]
                filename = neighbour[1]
                print "found neighbour ({}) in the {}.".format(filename,direction)
                join_lines(buffer_size,shp,filename)
                print "\n\n\n NEW ITERATION NEW ITERATION \n\n\n"
