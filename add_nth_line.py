# load into QGIS
# select n_th field to calculate
# calculates additional styling attributes for contour lines from lvl 9-14

#from qgis.core import *
#from qgis.gui import *
import processing

def create_lvl_copies(input_shp="DEFAULT",height_attr="height"):
    """
    creates zoom level dependent copies of 10 m spaced contour lines
    scale factor = {zoom-level : isoline spacing in m}
    used on selected layer
    """
    scale_factor = {9:500,10:200,11:100,12:50,13:20}
    if input_shp == "DEFAULT":
        layer = iface.mapCanvas().currentLayer()
        height_attr = "height"
    features = processing.features(layer)
    for level in range(9,14):
        export_features_per_lvl = []
        for feature in features:
            # can be divided by spacing -> must be contained in the dataset
            # change back to height
            if ((feature[height_attr] % scale_factor[level]) == 0):
                export_features_per_lvl.append(feature.id())
                print "selecting following ids:",len(export_features_per_lvl)
                print "current level is: "+str(level)+"; added feature: "+str(feature.id())+" with height: "+str(feature[height_attr])
        # select features that contain the specified criteria
        print "selecting following ids:",len(export_features_per_lvl)
        layer.setSelectedFeatures(export_features_per_lvl)

        # write down selected features
        basepath= iface.activeLayer().dataProvider().dataSourceUri()
        new_file = basepath[:-4]+"-level"+str(level)+".shp"
        # boolean 1 at the end saves only selected features
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, new_file, "utf-8", None, "ESRI Shapefile", 1)
        if error == QgsVectorFileWriter.NoError:
            print "Exported: ",new_file

create_lvl_copies("DEFAULT","height")


    # expr = QgsExpression( "\"ELEV\"=200" )
    # it = cLayer.getFeatures( QgsFeatureRequest( expr ) )
    # ids = [i.id() for i in it]
    # cLayer.setSelectedFeatures( ids )
    # print ids

def add_nth_line(level,elev,feature,parent):
    level_funcs = [add_nth_line_lev9,add_nth_line_lev10,add_nth_line_lev11,add_nth_line_lev12,add_nth_line_lev13,add_nth_line_lev14]
    try:
        return level_funcs[level-9](elev,feature,parent)
    except:
        print "please enter a level between 9 and 14"

# level 9
# spacing: 500 m
def add_nth_line_lev9(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0,5000
    if((elev == 0) or ((elev % 5000) == 0)):
        return 10
    # Matches e.g. 2500, 7500
    elif((elev % 2500) == 0):
        return 5
    # Matches e.g. 1000, 2000 etc.
    elif((elev % 1000) == 0):
        return 2
    # all others:
    else:
        return 1

# level 10
# contour spacing: 200 m
def add_nth_line_lev10(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0,2000,4000 etc
    if((elev == 0) or ((elev % 2000) == 0)):
        return 10
    # Matches e.g. 3000, 5000 etc.
    elif((elev % 1000) == 0):
        return 5
    # Matches e.g. 6200, 200 etc.
    elif((elev % 200) == 0):
        return 2
    # all others:
    else:
        return 1

# level 11
# spacing: 100 m
def add_nth_line_lev11(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0, 1000, 2000,4000 etc
    if((elev == 0) or ((elev % 1000) == 0)):
        return 10
    # Matches e.g. 1500, 2500 etc.
    elif((elev % 500) == 0):
        return 5
    # Matches e.g. 6200, 200 etc.
    elif((elev % 200) == 0):
        return 2
    # all others:
    else:
        return 1

# level 12
# spacing: 50 m
def add_nth_line_lev12(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0, 2000, 1000 etc
    if((elev == 0) or ((elev % 1000) == 0)):
        return 10
    # Matches e.g. 3750, 250, 750 etc.
    elif((elev % 250) == 0):
        return 5
    # Matches e.g. 6200, 200 etc.
    elif((elev % 200) == 0):
        return 2
    # all others:
    else:
        return 1

# level 13
# spacing:  20 m
def add_nth_line_lev13(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0, 200, 1200, 1000, 4000 etc
    if((elev == 0) or ((elev % 200) == 0)):
        return 10
    # Matches e.g. 100, 200 etc.
    elif((elev % 100) == 0):
        return 5
    # Matches e.g. 3960,40, etc.
    elif((elev % 40) == 0):
        return 2
    # all others:
    else:
        return 1

# level: 14
# spacing: 10 m
def add_nth_line_lev14(elev,feature,parent):
    # add 10th n_th line attribute to all matching isolines
    # e.g. 0,100,2500
    if((elev == 0) or ((elev % 100) == 0)):
        return 10
    # Matches e.g. 50, 150, etc.
    elif((elev % 50) == 0):
        return 5
    # Matches e.g. 20, 40, etc.
    elif((elev % 20) == 0):
        return 2
    # all others:
    else:
        return 1



# TESTING
# elev = 1000
# level = 10
# feature = None
# parent = None
# arg = add_nth_line(level,elev,feature,parent)
# print "add line function returened "+str(arg)+"; with level:"+str(level)+" and elev: "+str(elev)
#
# arg_direct = add_nth_line_lev10(elev,feature,parent)
# print "add line function returened arg_direct: "+str(arg)+"; with level:"+str(level)+" and elev: "+str(elev)
