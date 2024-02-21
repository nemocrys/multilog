from datetime import datetime
from PIL import Image
from pathlib import Path

#####################
folderToConvert = "measdata_2024-02-21_#01" # Folder has to be in the mutilog folder where it was created
convertToFormat = "jpeg" # "png" or "jpeg", not ".png"
#####################

pathlist = Path(f"../{folderToConvert}/").rglob("*.tiff")
for path in pathlist:
    starttime = datetime.now()
    newFilename = path.name.replace(".tiff",f".{convertToFormat}")
    newPath = Path(str(path.parent) + f"/{convertToFormat}s")
    newPath.mkdir(parents=True, exist_ok=True)
    newpathfilename = str(newPath) + "/" + newFilename
    
    with Image.open(path) as im:
        im.save(newpathfilename)
    endtime = datetime.now()
    duration = endtime - starttime
    print(f"{newpathfilename} : {duration}", end="\r")

print("Done.") 
