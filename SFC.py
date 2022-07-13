"""
geopandas for converting csv items to shapefiles..
and or extracting info from shapefiles..
splitting shapefiles..

codes
crs='EPSG:32750'  wgs84 z50s
crs='EPSG:28350'  gda94 zone 50
crs='EPSG:7850'  GDA2020 z50

data examples;
Long: 115.857
Lat: -31.9535
E = X: 391 285
N = Y: 6 464 746
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon, MultiPoint
import shapefile


class DataHandle():
    """
        class to load in csvs of information, which has some point data with X or Y columns. can create XYs from lat longs with the DataHandle.xy function.
        ie, ['Well Name', 'Epoch', 'TopDepth md', 'X', 'Y']
        
        can convert crs.
        can output csv into shapefile.

        Parameters
        ----------
        f : str :  the filepath

        Functions
        ---------
        read_file: read in the filepath. state whihc column is X, Y and the CRS. 
        convert_coords: convert crs if needed. 
        output_pointset_shapefile: save out file as shapefile with points datasets.


        Return
        ------
        all data is held in memory until its output, as a shapefile. """


    def __init__(self, f: str):
        self.file = f
        super().__init__()        

    def read_file(self, Xcol='X', Ycol='Y', crs='EPSG:28350'):
        print(f'openning file ...{self.file}...\n')
        self.data = pd.read_csv(self.file, index_col=0)
        print(self.data.columns)
        self.gdf = self.create_gdf(Xcol, Ycol, crs=crs)

    def create_gdf(self, Xcol, Ycol, crs):
        gdf = gpd.GeoDataFrame(self.data)
        gdf.set_geometry(gpd.points_from_xy(self.data[Xcol], self.data[Ycol]),inplace=True, crs=crs)# this creates a 'geometry' column of point data. 
        print('++ created gdf with crs ', gdf.crs.name)
        return gdf
        
    def output_pointset_shapefile(self):
        name = self.getname()
        self.gdf.to_file(f'D:\\Python Programming\\Oilies\\log\\{name}.shp')
        
    def getname(self):
        name =input('enter a output name for the shapefile ')
        return name

    def convert_pointset_coords(self, crs='EPSG:7850'):
        self.gdf = self.gdf.to_crs(crs)
        print('.. converted gdf to crs ', self.gdf.crs.name)

    def __str__(self):
        return f"""
        shapefile deets
          name: {self.file}
        """  


class ShapeClass(DataHandle):
    def __init__(self, f=''):
        super().__init__(f)
        DataHandle.__init__(self, f) # this line, lets outputs from the parent come back down to this child

    
    def convert_poly_coords(self, crs='EPSG:7850'):
        self.polygdf = self.polygdf.to_crs(crs)
        print('.. converted polygon_gdf to crs ', self.polygdf.crs.name)

    def create_polygon_from_pd(self, crs='crs'):
        """
        this will take all the xys in the csv and output one polygon cell. this can be exported as a polygon shapefile

        must be a way to loop and make use of the index=[onety]
        """

        X = self.data[['X']].to_numpy()
        Y = self.data[['Y']].to_numpy()
        poli = [(i,j) for i,j in zip(X, Y ) ]
        poli.append(poli[0]) #not needed?? but adds the same start point to the end. 3
        poly1 = Polygon(poli)
        self.polygdf = gpd.GeoDataFrame(index=['onety'], geometry=[poly1], crs=crs) # onety is the name of the shape.... so could be changed 
        print('++created polygon from all points in crs ', self.polygdf.crs.name )

    def create_polygon_from_file_with_numerous_ids(self, crs='crs'): 
        """
        this will take one csv file and split out all the IDs in a file and make polygons,
         then append them into one shapefile of polygons

        """
        ids=[]
        geoms=[]
        for name in self.data['ID'].unique():
            dp = self.data[self.data['ID']==name]
            poly1 = Polygon([(i,j) for i,j in zip(dp.X, dp.Y )])
            ids.append(name)
            geoms.append(poly1)

        df_polys = pd.DataFrame({'ID':ids, 'geometry': geoms})
        gdf = gpd.GeoDataFrame(index=df_polys['ID'], geometry=df_polys['geometry'], crs=crs) 
        
        print('exporting polygon shapfile from numerous IDs')
        named = self.getname()

        gdf.to_file(f"{named}.shp")
        pass

    def create_convex_hull(self, crs='crs'): # not working..?

        ch = self.polygdf.unary_union.convex_hull
        print('-----', [ch.wkt])
        poly = Polygon(ch.wkt)
        # self.polygdf = gpd.GeoDataFrame(index=['onety'], geometry=poly, crs=crs)
        

    def output_polygon_shapefile(self):
        print('exporting polygon shapfile')
        name = self.getname()
        self.polygdf.to_file(f"{name}.shp")




    def create_pointset_from_pd(self):  #not needed. replaced with create_gdf above.
        X = self.data[['X']].to_numpy()
        Y = self.data[['Y']].to_numpy()
        geopoints = MultiPoint([(i,j) for i,j in zip(X, Y)])
        return geopoints

    def read_shapefile(self, path: str):
        """
        load in shape files and strip the data... returns a pandas dataframe. 
        or just drag the shape .dbf into excel.
        """      

        #read in the file
        print('reading into df ', path)
        shapeRead = shapefile.Reader(path)

        #And save out some of the shape file attributes
        recs    = shapeRead.records()
        shapes  = shapeRead.shapes()
        fields  = shapeRead.fields
        Nshp    = len(shapes)

        shapeRead.shapeTypeName 
        rec= shapeRead.record(0)
        # rec['TopElev']
        #print the point values of the first 5 shapes
        # for i in range(5):
        #     print(shapes[i], '\n',
        #     shapes[i].points)#, shapes[i].z )


        fields = [x[0] for x in shapeRead.fields][1:]
        shps = [s.points for s in shapeRead.shapes()]
        recs= shapeRead.records()

        df = pd.DataFrame(columns=fields, data=recs)
        df = df.assign(coords=shps)
        self.data=df
        # print(df.describe(include='all'))
        # return df

    def create_dug_dupoly_polygon(self, named='', crs='crs'):
        """
        this will turn a dataframe of x,y points wiht an ID collumn into a DUG polygon file. output as dupoly.
        """

        coords_inverted = {4:'old', 'EPSG:32750':'WGS 84 / UTM zone 50S', 'EPSG:28350':'GDA94 / MGA zone 50', 'EPSG:7850': 'GDA2020 / MGA zone 50'}
        crs=coords_inverted[crs]

        header = f'''name "{named}"
verticalDimension time
lineColour rgb(0,0,0)
fillColour rgb(80,80,80)
lineThickness 2.0
fillPolygon true
type MAP
projectCRS
    name "{crs}"
    authority EPSG
    code 7850
value 0.0\n'''
        body=''
        for id in self.data['ID'].unique():
            dp = self.data[self.data['ID']==id]
            body+='points\n'
            for _, row in dp.iterrows():
                body+=f"    {row['X']} {row['Y']}\n"

        with open(f'{named}.dupoly', 'w') as f:
            f.write(header+body)
        pass


def main():
    f = 'D:/Python Programming/Oilies/log/testset.csv'

    coords = {4:'old', 3:'EPSG:32750', 2: 'EPSG:28350', 1: 'EPSG:7850'}

    ''' coords chooser
       [4] 60s..
       [3] wgs84 z50s 'EPSG:32750'
       [2] gda94 z50  'EPSG:28350'
       [1] GDA2020 z50  'EPSG:7850' 
    '''   

    ######   loading and converting pointset data, outputs a pointset shapefile.. 
    s = ShapeClass(f) 
    # s.read_file(Xcol='X', Ycol='Y', crs=coords[2])
    # s.convert_pointset_coords(crs=coords[1])
    # s.output_pointset_shapefile()


    ##### load and create a polygon from points in the csv... 

    # s.create_polygon_from_pd(crs=coords[2])
    # s.convert_poly_coords(crs=coords[1])
    # # s.create_convex_hull()

    # s.output_polygon_shapefile()
    

    #####  strip info from a shapefile and create a pandas df
    # shapef = 'D:/Python Programming/Oilies/log/CCM_Faults.shp'
    # s.read_shapefile(shapef)
    # print(s.data)


    #### working with a shapefile that is currently several polygons, but as point sets.. i want them all as polygons
    ### loading and converting to a polygon. 
    # shapef = 'D:/Python Programming/Oilies/log/CCM_Faults.shp'
    # s.read_shapefile(shapef)
    # # s.create_polygon_from_pd(crs=coords[2]) # this mashes it all into one polygon.. 
    # # s.convert_poly_coords(crs=coords[1])

    # s.create_polygon_from_file_with_numerous_ids(crs=coords[1]) # this makes several polygs into one file.. 
    
    # s.output_polygon_shapefile()


    ####  create a dug polygon file from file. 
    shapef = 'D:/Python Programming/Oilies/log/CCM_Faults.shp'
    s.read_shapefile(shapef)
    # print(df)

    s.create_dug_dupoly_polygon(named='testingdugy', crs=coords[1])

    print('done')

if __name__=='__main__':
    main()