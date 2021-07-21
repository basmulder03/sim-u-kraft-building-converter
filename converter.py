from nbt.nbt import *
import json
from collections import OrderedDict
from os import path, makedirs
from glob import glob
import clipboard
import traceback

block_data_file_name = 'block_data.json'


# create a class to store the properties of a block in
class BlockProperties:
    def __init__(self, name = "", properties = {}):
        self.name = name
        self.properties = properties

    def __str__(self):
        return "name="+self.name + ", properties=" + self.properties.__str__()

    def hasProperties(self):
        return len(self.properties.keys()) > 0


# open the block data json file
def get_json():
    with open(block_data_file_name) as f:
        return json.load(f)

# update the json in the block data json file
def replace_json(json_data):
    with open(block_data_file_name, "w") as f:
        json.dump(json_data, f, indent=2, sort_keys=True)

# add a block to the json
def add_block_to_json(block_dict):
    # get the json from the file
    json_blocks = get_json()
    # loop through the key value pairs in the dictionary (json file)
    for key, value in block_dict.items():
        # check if the block has properties, if not add an empty dictionary
        if not key in json_blocks:
            json_blocks[key] = {}
        # loop through the items inside the properties object
        for iKey, iValue in value.items():
            # add the properties to the dictionary
            json_blocks[key][iKey] = iValue
        # replace the old json code with the new json code
        replace_json(json_blocks)
    # return the block data json file in dictionary format
    return json_blocks

# get the data for a new block
def get_data_for_new_block(which_block_to_get_data_for):
    [block, subtype] = which_block_to_get_data_for.split(':')
    print(f"/setblock ~1 ~1 ~ %s %s" % block, subtype)
    # create setblock command to get the block
    clipboard.copy(f"/setblock ~1 ~1 ~ %s %s" % block, subtype)
    # print the id of the block
    print("Create an alias for the block with the id: " + which_block_to_get_data_for)
    # give that block an name
    name = input("What is the name of the block? ")

    # create an empty properties object
    properties = {}
    # loop indefinately to add all the block properties to the file
    while True:
        # get the name of the property
        prop_name = input("What is the name of the property? (leave blank if there are no properties left to add) ")
        # if no prop name, skip out of the loop
        if not prop_name:
            break
        # if there was a property name, give that property a value
        prop_value = input("What is the value of the property " + prop_name + "? ")
        # add the property to the dictionary
        properties[prop_name] = prop_value
    # add the block to the json file
    return add_block_to_json({block: {subtype:{"name":name, "properties": properties}}})

# check if the block exists currently in the json file
def check_if_block_exists(block_id):
    # get the block and the subtype of the block
    [block, subtype] = block_id.split(":")
    # get the json data from the file
    block_data = get_json()
    # check if the block is not inside the json file, and if that is not the case check if the subtype is already in the json file
    if not block in block_data or not subtype in block_data[block]:
        # if the above mentioned conditions are not true, create a new block for in the json file and update the block_data variabele
        block_data = get_data_for_new_block(block_id)
    # get the block data from the json dictionary
    data = block_data[block][subtype]
    # return the properties of that block
    return BlockProperties(data['name'], data['properties'])

# method to create a nbt file from the old txt file
def create_nbt_file(file, typeid, output_path):
    if "\\" in file:
        file_data = file.split("\\")[-1]
    else:
        file_data = file
    # get the new name of the file
    name = file_data.split(".")[0]
    name = name.replace(" ", "_")
    name = name.lower()

    # make an author variabele and set the default to unknown
    author = TAG_String(name="author", value="unknown")

    # set the typeid for the file
    typeid = TAG_Int(name='typeID', value=typeid)

    # set the name for the name property
    inner_name = name

    # remove pkid from the inner file name
    if "pkid" in name:
        inner_name = name.split("-")[1]

    # set the value of the inner file name
    name_nbt = TAG_String(name="name", value=inner_name)

    # create an ordered dictionary
    key_value_map = OrderedDict()

    # create a new nbt file object
    nbtfile = NBTFile()

    # set the name of the nbt file
    nbtfile.name = 'NTBFile'

    # open the txt file with read privileges
    file = open(file, 'r+')
    # get all the different lines of the file
    lines = file.readlines()

    # remove the \n from the files
    lines = [x.replace('\n', '') for x in lines]

    # create a size tag
    sizeList = TAG_List(name="size", type=TAG_Int)

    # get the x, y and z values of the txt file
    [x, z, y] = [int(value) for value in lines[0].split('x')]

    # put the x, y and z values inside the size list
    sizeList.tags.extend([
        TAG_Int(x),
        TAG_Int(y),
        TAG_Int(z)
    ])

    # create the palette compound
    paletteList = TAG_List(name='palette', type=TAG_Compound)

    # loop through all the different blockTypes
    for blockType in lines[1].split(';'):
        # try to run this without errors
        try:
            # check if there is an equals sign inside the string
            if '=' in blockType:
                # if that is the case split on the equals sign
                [key, value] = blockType.split('=')
            # if the key is equals to AU update the author name, from the default unknown to the author name
            if (key == 'AU'):
                author = TAG_String(name='author', value=value) 
                # and skip the rest of the code
                continue
            # get the data of the block
            block_data = check_if_block_exists(value)
            # create a key value pair on that key with the name value
            key_value_map[key] = block_data
            print(f"added %s to the dict" % str(block_data))
        # if there is an error show a message
        except:
            traceback.format_exc()

    # set the simukraft block ids
    key_value_map['$'] = BlockProperties("simukraft:control_block")
    key_value_map['*'] = BlockProperties("simukraft:light_white")
    key_value_map['!'] = BlockProperties("minecraft:air")
	
	# loop through the key value pairs inside the keyvalue map and create compound tags to save them to the nbt file
    for key, value in key_value_map.items():
        compound = TAG_Compound()
        # add a new to the compound
        compound.tags.append(
            TAG_String(name='Name', value=value.name)
        )
        # check if the block has properties
        if value.hasProperties():
            # if that is the case set all the properties
            properties_list = TAG_List(type=TAG_String, name="Properties")

            for key, value in value.properties.items():
                properties_list.tags.append(TAG_String(name=key, value=value))
            compound.tags.append(properties_list)
        paletteList.tags.append(compound)

    # get the structure from teh file
    blockLines = lines[2:]

    # create a blocks compound
    blockList = TAG_List(name='blocks', type=TAG_Compound)
    size = 0

    # create a counter for the count of blocks inside the building
    blocksinbuilding = 0

    # loop through all the different y levels of the building
    for ylist in range(y):
        # create a sublist of the line with the blocks of that y level
        curList = blockLines[ylist]
        # loop through all the blocks in the z direction
        for zlist in range(z):
            # get all the x values for the current z
            curPart = curList[zlist * x:zlist * x + x]

            # loop through all the values inside the curPart sublist
            for xlist in range(x):
                try:
                    # get the index of the position of the current block
                    curIndex = int(list(key_value_map.keys()).index(curPart[xlist]))
                    # if the letter of the block is not equals to A, add a block to the total block counter (A always has the value air assigned to it.)
                    if not curPart[xlist] == "A":
                        blocksinbuilding += 1
                except:
                    # print the stacktrace
                    traceback.print_exc()
                    # give a helpful message to the user 😁
                    print(str(curPart[xlist]) + " was not found, substituting with air.")
                    # get the index of an air block to substitute the not found
                    curIndex = int(list(key_value_map.keys()).index("A"))
                # create a new compound tag
                compound = TAG_Compound()
                # create a position list for the compound tag
                intList = TAG_List(name='pos', type=TAG_Int)
                # set the position equals to the current x, y and z values
                intList.tags.extend([TAG_Int(xlist),TAG_Int(ylist),TAG_Int(zlist)])
                # add the position and the state (the position of the block state data) to the compound
                compound.tags.extend([
                    intList,
                    TAG_Int(name='state', value=curIndex)
                ])
                # add the compound to the blocklist
                blockList.tags.append(compound)

    # calculate the cost and the rent of the buildings
    rent = blocksinbuilding * 0.01
    cost = blocksinbuilding * 0.02

    # add the cost and the rent tags
    rent = TAG_Float(name='rent', value=rent)
    cost = TAG_Float(name='cost', value=cost)

    # create a data version tag
    dataVersion = TAG_Int(name='DataVersion', value=2580)

    # add all the created tags to the root tags
    nbtfile.tags.extend([
        sizeList,
        paletteList,
        blockList,
        author,
        cost,
        dataVersion,
        name_nbt,
        rent,
        typeid

    ])
    # create the nbt file
    nbtfile.write_file(filename="{0}/{1}.nbt".format(output_path, name))

# get the path to the old txt files
path_to_old_files = input("Which path are the files located at?: ")
# get an array of the relative paths to the .txt files in that folder
files = glob(f"%s/*.txt" % path_to_old_files)

# get a path to output the newly created nbt files in
path_to_new_files = input("Which path to output the nbt files at?: ")

# create that new path if that path doesn't exists yet
if not path.exists(f"./%s" % path_to_new_files):
    makedirs(f"./%s" % path_to_new_files)

# show a messsage to say how many files have to be converted
print("Converting " + str(len(files)) + " files")

# ask for the typeid of the building
typeid = int(input("What is the type id of the files in this folder? "))

# create a local index
index = 0

# loop through all the txt files in the selected folder
for file in files:
    # add one to the index
    index += 1
    # show a message to convey how much progress the program has made
    print("Converting " + file + " (" + str(index) + "/" + str(len(files)) + ")")
    # create a nbt file for every one of the txt files
    create_nbt_file(file, typeid, path_to_new_files)

