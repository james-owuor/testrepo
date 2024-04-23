 # #Finding optimal locations of new stores using Decision Optimization
# #A fictional coffee company plans to open N shops in the near future and needs
# #to determine where they should be located
# #we use chicago open data for this example
# #we implement a K-Median model to get the optimal location of our future shops
#
#        #Step 1 import the DOcplex package
# import sys
# import docplex.mp
# import requests
#
#
# #step 2 Model the data
# #the data is composed of the list of the public libraries and their geo locations
# #the data is acquired from Chicago open data as a JSON file
#        #step 3 Prepare the data
# #we need to collect the list of public libraries locations and keep their names, latitudes and longitudes
#
# #store longitude,latitude and street crossing of each public library location.
# class XPoint(object):
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y
#     def __str__(self):
#         return "P(%g_%g)" %(self.x, self.y)
#
# class NamedPoint(XPoint):
#     def __init__(self, name, x, y):
#         XPoint.__init__(self, x, y)
#         self.name = name
#     def __str__(self):
#         return self.name
# #define how to compute the earth distance between 2 points: we use geopy
# from geopy.distance import great_circle
# def get_distance(p1, p2):
#     return great_circle((p1.y, p1.x), (p2.y, p2.x)).miles
#
# # Declare the list of libraries: parse the JSON file to get the list of libraries
# # and store them as Python elements
# def build_libraries_from_url(url, name_pos, lat_long_pos):
#     import requests
#     import json
#     r= requests.get(url)
#     myJson= r.json()
#     print(myJson)
#     myJson= myJson["data"]
#     Libraries= []
#     k = 1
#     for location in myJson:
#         uname= location[name_pos]
#         try:
#             latitude = float(location[lat_long_pos][1])
#             longitude = float(location[lat_long_pos][2])
#         except TypeError:
#             latitude=longitude=None
#         try:
#             name= str(uname)
#         except:
#             name= "???"
#         name= "P_%s_%d" %(name, k)
#         if latitude and longitude:
#             cp = NamedPoint(name, longitude, latitude)
#             Libraries.append(cp)
#             k+= 1
#     return Libraries
#
# Libraries=build_libraries_from_url('https://data.cityofchicago.org/api/views/x8fc-8rcq/rows.json?accessType=DOWNLOAD', name_pos= 10, lat_long_pos=16)
# print("There are %d public libraries in Chicago" %(len(Libraries)))
#
# #Define the number of shops to open
# #create a constant that indicates how many coffee shops we would like to open
# nb_shops = 5
# print("We would like to open %d coffee shops" %nb_shops)
# #Validate the data by dsiplaying them
# #we will use the folium library to display a map with markers
# import folium
# map_osm= folium.Map(location=[41.878, -87.629], zoom_start= 11)
# for library in Libraries:
#     lt= library.y
#     lg= library.x
#     folium.Marker([lt, lg]).add_to(map_osm)
# map_osm
# #the data is displayed but it is impossible to determine where to ideally open the coffee shops b just looking at the map
# #Lets set up DPcplex to write and solve an optimization model that will help us determine where to locate the coffee shops in an optimal way
#        #Step 4 : Set up the prescriptive model
# from docplex.mp.environment import Environment
# env= Environment()
# env.print_information()
# #create the DOcplex model
# from docplex.mp.model import Model
# mdl= Model("coffee shops")
# #Define the decision variables
# BIGNUM = 999999999
# # Ensure unique points
# Libraries = set(Libraries)
# # For simplicity, let's consider that coffee shops candidate locations are the same as libraries locations.
# # That is: any library location can also be selected as a coffee shop.
# coffeeshop_locations = Libraries
# # Decision vars
# # Binary vars indicating which coffee shop locations will be actually selected
# coffeeshop_vars= mdl.binary_var_dict(coffeeshop_locations, name="is_coffeeshop")
# #Binary vars representing the "assigned" libraries for each coffee shop
# link_vars= mdl.binary_var_matrix(coffeeshop_locations, Libraries, "link")
# #Express the business constraints
# #first constraint: if the distance is suspect, it needs to be excluded from the problem
# for c_loc in coffeeshop_locations:
#     for b in Libraries:
#         if get_distance(c_loc, b) >= BIGNUM:
#             mdl.add_constraint(link_vars[c_loc, b] == 0, "ct_forbid_{0!s}_{1!s}".format(c_loc, b))
# #second constraint: each library must be linked to a coffee shop that is open
# mdl.add_constraints(link_vars[c_loc, b] <= coffeeshop_vars[c_loc]
#                     for b in Libraries
#                     for c_loc in coffeeshop_locations)
# mdl.print_information()
# #Third constraint: each library is linked to exactly one coffee shop
# mdl.add_constraints(mdl.sum(link_vars[c_loc, b] for c_loc in coffeeshop_locations) == 1
#                     for b in Libraries)
# mdl.print_information()
# #fourth constraint:there is a fixed number of coffee shops to open
# #total nb of open coffee shops
# mdl.add_constraint(mdl.sum(coffeeshop_vars[c_loc] for c_loc in coffeeshop_locations) == nb_shops)
# mdl.print_information()
# #Express the objective
# #the objective is to minimize the total distance from libraries to coffee shops so that a book reader alwys gets to our coffee shop easily
# #minimize total distance from points to hubs
# total_distance = mdl.sum(link_vars[c_loc, b] * get_distance(c_loc, b) for c_loc in coffeeshop_locations for b in Libraries)
# mdl.minimize(total_distance)
# #solve with the decision optimization solve service
# print("#coffee shops locations = %d" % len(coffeeshop_locations))
# print("# coffee shops           =%d" %nb_shops)
# assert mdl.solve(), "!!! Solve if the model fails"
#    #step 5 investigate the solution and run an example analysis? display the location of coffee shops on a map
# total_distance = mdl.objective_value
# open_coffeeshops = [c_loc for c_loc in coffeeshop_locations if coffeeshop_vars[c_loc].solution_value == 1]
# not_coffeeshops = [c_loc for c_loc in coffeeshop_locations if c_loc not in open_coffeeshops]
# edges = [(c_loc, b) for b in libraries for c_loc in coffeeshop_locations if int(link_vars[c_loc, b]) == 1]
#
# print("Total distance = %g" % total_distance)
# print("# coffee shops  = {0}".format(len(open_coffeeshops)))
# for c in open_coffeeshops:
#     print("new coffee shop: {0!s}".format(c))
#    #displaying the solution
# import folium
# map_osm=folium.Map(location=[41.878, -87.629], zoom_start=11)
# for coffeeshop in open_coffeeshops:
#     lt= coffeeshop.y
#     lg= coffeeshop.x
#     folium.Marker([lt, lg], icon=folium.Icon(color="red", icon= "info-sign")).add_to(map_osm)
# for b in Libraries:
#     if b not in open_coffeeshops:
#         lt=b.y
#         lg=b.x
#         folium.Marker([lt,lg]).add_to(map_osm)
# for (c, b) in edges:
#     coordinates= [[c.y,c.x],[b.y, b.x]]
#     map_osm.add_child(folium.PolyLine(coordinates, color="#FF0000", weight=5))
# map_osm.show_in_browser()

