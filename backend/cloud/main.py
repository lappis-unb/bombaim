import os
import json
from google.cloud import storage

from mma.MMA import gbl
from mma.MMA import auto
from mma.MMA import midi
from mma.MMA import tempo
from mma.MMA import parse
from mma.MMA import paths
from mma.MMA import grooves
from mma.MMA import userGroove
from mma.MMA.auto import loadDB


headers = {
    'Access-Control-Allow-Origin': '*'
}

storage_client = storage.Client()

def create_groove(request):
    created = save_groove()
    msg = "ERROR"
    if created:
        msg = "CREATED"
    
    return (msg, 200, headers)

def save_groove():
    bucket = storage_client.get_bucket("mma-bombaim")

    new_groove = bucket.blob("lib/bombaim/new_groove.mma")
    
    new_groove.upload_from_string("BETA TEST")

    return True

def update_grooves(event, context):
    # Read and copy files from mma storage #   
    mma_bucket = storage_client.get_bucket("mma-bombaim")
    blobs = mma_bucket.list_blobs()
    
    for blob in blobs:
        filename = "/tmp/mma/"+str(blob.name)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        blob.download_to_filename(filename)

    # Run MMA update groves list #
    # Clear global variables and change MMAdir
    gbl.__init__()
    gbl.MMAdir = "/tmp/mma/"
    # Set paths for the libs
    paths.init()

    gbl.makeGrvDefs = 1

    try:
        auto.libUpdate()
    except SystemExit:
        print("ignoring SystemExit", flush=True)

    # Needed import for global variable libDirs after paths.init() method ran
    from mma.MMA.paths import libDirs

    # Get grooves from MMA update #
    grooves = {}
    for lib in libDirs:
        g = loadDB(lib)
        if g:
            for g_path in g:
                name = g_path.split("/")[-1].split(".")[0]
                gs = g[g_path]

                if name in grooves:
                    og = grooves[name]
                    gs = og + gs

                grooves.update({name: gs})
    
    # Update file at storage #
    groove_bucket = storage_client.get_bucket("grooves-bombaim")
    groove_blob = groove_bucket.blob('grooves/list_grooves.json')    
    groove_blob.upload_from_string(json.dumps(grooves))    
    groove_blob.make_public()
