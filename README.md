# DEM-Processing-Pipeline
Creates Hillshade and 10 m spaced contour lines for the use in online maps.

## Create seemless contour lines

### 1. Download DEM Data
Good datasets for Europe can be found here: http://www.eea.europa.eu/data-and-maps/data/eu-dem

### 2. Batch Reproject DEM Raster data to EPSG:3857
Navigate to download directory and reproject all raster files. Currently processes on 4 kernels.
```
ls -1 *.tif | tr '\n' '\0' | tr -d ".tif" | xargs -0 -n 1 -P 4 -I {} gdalwarp -s_srs EPSG:3035 -t_srs EPSG:3857 -r average {}.tif {}_3857.tif
```
### 3. Crop all rasters into small tiles of 500x500 km
This process can be easily done with QGIS / ArcGIS, e.g. with the GridSplitter Plugin and `data/grid_500x500m_3857.shp`.

### 4. Create a set of clean contours
The scripts runs through the directory of tiled rasters, creates a contour dataset for each of them. Additionally it creates a buffer zone for each raster and calculates the contour lines at the raster edges to obtain smooth contour datasets. Furthermore it deletes small features with a length < 1000 m.
```
python clean_contours.py
```

### 5. Clean dataset
Manually with QGIS

### 6. Add additional information for map rendering
Run the `create_lvl_copies` function inside QGIS to obtain several versions of contour line datasets, which are optimized for their specific zoom level.
```
QGIS Python Terminal: add_nth_line.py
```

## Create Hillshade dataset
`clean_contours.py` creates a vrt dataset of all tiled raster sources. This can be used to obtain a merged hillshade raster file.
Alternatively, the tile structure can be preserved and the raster tiles can be "hillshaded" individually using following batch command:
```
ls -1 *.tif | tr '\n' '\0' | tr -d ".tif" | xargs -0 -n 1 -P 4 -I {} gdaldem hillshade {}.tif {}_hillshade.tif -z 1.0 -s 1.0 -az 315.0 -alt 45.0 -of GTiff
```
