import requests
from requests.auth import HTTPDigestAuth
import json
import os
from PIL import Image
from io import BytesIO

key = "b866417bd1dbe7afdd2e38d765848f8d"
mainurl = "https://rebrickable.com/api/v3/lego/"
kitID = '76424'

def getPartsList(url):
    # It is a good practice not to hardcode the credentials. So ask the user to enter credentials at runtime
    myResponse = requests.get(url,params={"key": key, 'inc part_details' : '1'})
    if(myResponse.ok):
        # Loading the response data Into a dict Variable
        # json.loads takes in only binary or string variables so using content to fetch binary content
        # loads (Load String) takes a Json file and converts into python data structure (dict or list, depending on JSON)
        jData = json.loads(myResponse.content)
        return jData
    else:
        # If response code is not ok (200), print the resulting http error code with description
        myResponse.raise_for_status()

def getSetPartsList(kitID):
    url = mainurl + "sets/" + kitID + "-1/parts/"
    partsList = getPartsList(url)

    # print list
    json_str = json.dumps(partsList, indent=4)
    print(json_str)
    
    # Save the dictionary as a JSON file
    with open('data.json', 'w') as f:
        json.dump(partsList, f)

    return partsList

def simplifiyPartsList(inventory):
    # Initialize an empty dictionary for the simplified inventory
    simplified_inventory = {}
    
    # Iterate over each item in the original inventory
    for item in inventory["results"]:
        if item["is_spare"]:
            continue
    
        # Get the part number
        part_num = item["part"]["part_num"]
    
        # If the part number is not in the simplified inventory, add it
        if part_num not in simplified_inventory:
            simplified_inventory[part_num] = {
                "part_num": part_num,
                "name": item["part"]["name"],
                "part_url": item["part"]["part_url"],
                "part_img_url": item["part"]["part_img_url"],
                "colors": []
            }
    
        # Add the color and quantity to the part's list of colors
        simplified_inventory[part_num]["colors"].append({
            "color": item["color"]["name"],
            "quantity": item["quantity"]
        })
    
    # Print the simplified inventory as a JSON string
    print(json.dumps(simplified_inventory, indent=4))

    return simplified_inventory

    
