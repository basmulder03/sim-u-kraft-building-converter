from nbt.nbt import *
import json
from collections import OrderedDict
from os import path, mkdir, getcwd
from glob import glob

block_data_file_name = 'block_data.json'

class BlockProperties:
    def __init__(self, name = "", properties = {}):
        self.name = name
        self.properties = properties

    def __str__(self):
        return "name="+self.name + ", properties=" + self.properties.__str__()

    def hasProperties(self):
        return len(self.properties.keys()) > 0


def get_json():
    with open(block_data_file_name) as f:
        return json.load(f)

def replace_json(json_data):
    with open(block_data_file_name, "w") as f:
        json.dump(json_data, f, indent=2, sort_keys=True)

def add_block_to_json(block_dict):
    json_blocks = get_json()
    for key, value in block_dict.items():
        if not key in json_blocks:
            json_blocks[key] = {}
        for iKey, iValue in value.items():
            json_blocks[key][iKey] = iValue
        replace_json(json_blocks)
    return json_blocks

def get_data_for_new_block(which_block_to_get_data_for):
    print("Create an alias for the block with the id: " + which_block_to_get_data_for)
    name = input("What is the name of the block? ")
    [block, subtype] = which_block_to_get_data_for.split(':')
    properties = {}
    while True:
        prop_name = input("What is the name of the property? (leave blank if there are no properties left to add) ")
        if not prop_name:
            break
        prop_value = input("What is the value of the property " + prop_name + "? ")
        properties[prop_name] = prop_value
    return add_block_to_json({block: {subtype:{"name":name, "properties": properties}}})

def check_if_block_exists(block_id):
    [block, subtype] = block_id.split(":")
    block_data = get_json()
    if not block in block_data or not subtype in block_data[block]:
        block_data = get_data_for_new_block(block_id)
    data = block_data[block][subtype]
    return BlockProperties(data['name'], data['properties'])


def create_nbt_file(file, typeid):

    name = file.split(".")[0]

    name = name.replace(" ", "_")
    name = name.replace(" ", "_")
    name = name.replace("&", "")
    name = name.replace("!", "")
    name = name.replace("(", "")
    name = name.replace(")", "")
    name = name.replace("+", "")
    name = name.lower()
    if "pkid" in name:
        name = name.split("-")[1]

    author = TAG_String(name="author", value="unknown")

    typeid = TAG_Int(name='typeID', value=typeid)

    inner_name = name

    # if "pkid" in name:
    #    inner_name = name.split("-")[1]

    name_nbt = TAG_String(name="name", value=inner_name)
    key_value_map = OrderedDict()

    nbtfile = NBTFile()

    nbtfile.name = 'NTBFile'


    file = open(file, 'r+')
    lines = file.readlines()

    lines = [x.replace('\n', '') for x in lines]

    sizeList = TAG_List(name="size", type=TAG_Int)

    [x, z, y] = [int(value) for value in lines[0].split('x')]

    sizeList.tags.extend([
        TAG_Int(x),
        TAG_Int(y),
        TAG_Int(z)
    ])


    paletteList = TAG_List(name='palette', type=TAG_Compound)

    for blockType in lines[1].split(';'):
        try:
            if '=' in blockType:
                [key, value] = blockType.split('=')
            if (key == 'AU'):
                author = TAG_String(name='author', value=value) 
                continue
            block_data = check_if_block_exists(value)
            key_value_map[key] = block_data
        except:
            print("Oops, something went wrong.")

    key_value_map['$'] = BlockProperties("simukraft:control_block")
    key_value_map['*'] = BlockProperties("simukraft:light_white")
    key_value_map['!'] = BlockProperties("minecraft:air")
	
	
    for key, value in key_value_map.items():
        compound = TAG_Compound()
        compound.tags.append(
            TAG_String(name='Name', value=value.name)
        )
        if value.hasProperties():
            properties_list = TAG_List(type=TAG_String, name="Properties")

            for key, value in value.properties.items():
                properties_list.tags.append(TAG_String(name=key, value=value))
            compound.tags.append(properties_list)
        paletteList.tags.append(compound)

    blockLines = lines[2:]

    blockList = TAG_List(name='blocks', type=TAG_Compound)
    size = 0

    blocksinbuilding = 0

    for ylist in range(y):
        curList = blockLines[ylist]
        for zlist in range(z):
            curPart = curList[zlist * x:zlist * x + x]
            for xlist in range(x):
                try:
                    curIndex = int(list(key_value_map.keys()).index(curPart[xlist]))
                    if not curPart[xlist] == "A":
                        blocksinbuilding += 1
                except:
                    print(str(curPart) + " was not found, substituting with air.")
                    curIndex = int(list(key_value_map.keys()).index("A"))
                compound = TAG_Compound()
                intList = TAG_List(name='pos', type=TAG_Int)
                intList.tags.extend([TAG_Int(xlist),TAG_Int(ylist),TAG_Int(zlist)])
                compound.tags.extend([
                    intList,
                    TAG_Int(name='state', value=curIndex)
                ])
                blockList.tags.append(compound)

    rent = blocksinbuilding * 0.01
    cost = blocksinbuilding * 0.02

    rent = TAG_Float(name='rent', value=rent)
    cost = TAG_Float(name='cost', value=cost)

    dataVersion = TAG_Int(name='DataVersion', value=2580)

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
    nbtfile.write_file(filename="nbt/"+name+".nbt")

if not path.exists("nbt"):
    mkdir("nbt")

files = glob('*.txt')

print("Converting " + str(len(files)) + " files")

typeid = int(input("What is the type id of the files in this folder? "))

index = 0

for file in files:
    index += 1
    print("Converting " + file + " (" + str(index) + "/" + str(len(files)) + ")")
    create_nbt_file(file, typeid)

