import zipfile
import os

def create_zip(file_paths, zip_name="files.zip"):

    with zipfile.ZipFile(zip_name, 'w') as z:
        for file in file_paths:
            if os.path.exists(file):
                z.write(file)

    return zip_name
