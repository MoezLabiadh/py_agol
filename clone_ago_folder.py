'''
Make a copy of a folder
'''
from arcgis.gis import GIS

# connect to your org
gis = GIS(
    'https://governmentofbc.maps.arcgis.com', 
    'XXX',
    'XXX',
    verify_cert=False
) 

# 2. get your User object
me = gis.users.me

# 3. set folder titles
src_folder_name = "Survey-5NP _test"
dst_folder_name = "Survey-5NP _test Copy"

# 4. find the source folder’s ID
src = next((f for f in me.folders if f["title"] == src_folder_name), None)
if not src:
    raise ValueError(f"Folder '{src_folder_name}' not found.")
src_id = src["id"]

# 5. find or create the destination folder and get its ID
dst = next((f for f in me.folders if f["title"] == dst_folder_name), None)
if dst:
    dst_id = dst["id"]
else:
    folder_info = gis.content.create_folder(dst_folder_name,
                                           owner=me.username)
    dst_id = folder_info['id']

# 6. list items in the source folder
items_to_clone = list(me.items(folder=src_id, max_items=1000))

# 7. clone them into the new folder
cloned = gis.content.clone_items(
    items=items_to_clone,
    folder=dst_id,
    copy_data=True
)

print(f"Cloned {len(cloned)} items into '{dst_folder_name}'")
