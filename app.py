from flask import Flask, Blueprint, render_template, request, send_file
from flask_bower import Bower
import io
from os import environ
import datetime
import string
import json

import cv2
import numpy as np
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec

from datetime import datetime, timedelta
from azure.storage.filedatalake import DataLakeServiceClient

views = Blueprint('views', __name__, template_folder='templates')

app = Flask(__name__)

Bower(app) 

app.register_blueprint(views)

def log(f, message):
   f.write(str(datetime.now()))
   f.write(' : ')
   f.write(message)
   f.write('\n')
   f.flush()

def get_configuration():    
   account_key = None
   account_name = None
   container_name = None
   debug_file = None

   try:
      import configuration as config

      account_name = config.ACCOUNT_NAME
      container_name = config.CONTAINER_NAME
      debug_file = config.DEBUG_FILE
   except ImportError:
      pass

   try:
      import keys as keys
      account_key = keys.ACCOUNT_KEY

   except ImportError:
      pass

   account_key = environ.get('ACCOUNT_KEY', account_key)
   account_name = environ.get('ACCOUNT_NAME', account_name)
   container_name = environ.get('CONTAINER_NAME', container_name)
   debug_file = environ.get('DEBUG_FILE', debug_file)
 
   return {
      "account_key": account_key,
      "account_name": account_name,
      'container_name': container_name,
      'debug_file': debug_file
   }   

configuration = get_configuration()

f = open(configuration['debug_file'], 'a')
log(f, "Starting...")
f.close()

@app.route("/list", methods=["GET"])
def list():
   configuration = get_configuration()
   
   f = open(configuration['debug_file'], 'a')

   try:
      global service_client
 
      log(f, "[LIST] Account Name: '{}'".format(configuration['account_name']))
      log(f, "[LIST] Account Key: '{}'".format(configuration['account_key']))
      log(f, "[LIST] Container: '{}'".format(configuration['container_name']))

      service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format("https", configuration['account_name']), credential=configuration['account_key'])

      log(f, '[LIST] DataLakeServiceClient - Login successful')

      file_system_client = service_client.get_file_system_client(file_system=configuration['container_name'])
      
      log(f, '[LIST] File System - Login successful')

      output = []

      paths = file_system_client.get_paths(path="/")

      for path in paths:
         log(f, "[LIST] File Found - {}".format(path.name))
         output.append({
            "file_name": path.name
         })

         log(f, 'File: ' + path.name)

      log(f, 'File System - List Completed')

      f.close()

      return json.dumps(output, sort_keys=True)

   except Exception as e:
      log(f, str(e))

      f.close()

      output.append({
         "status" : 'fail',
         "error" : str(e)
      })
      
      return json.dumps(output, sort_keys=True),

@app.route("/retrieve", methods=["GET"])
def retrieve():
   output = []
   
   try:
      configuration = get_configuration()

      f = open(configuration['debug_file'], 'a')
      
      file_name = request.values.get('filename')
 
      log(f, "[RETRIEVE] Account Name: '{}'".format(configuration['account_name']))
      log(f, "[RETRIEVE] Account Key: '{}'".format(configuration['account_key']))
      log(f, "[RETRIEVE] Container: '{}'".format(configuration['container_name']))
      log(f, "[RETRIEVE] File Name: {}'".format(file_name))
 
      service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format("https", configuration['account_name']), credential=configuration['account_key'])

      log(f, '[RETRIEVE] DataLakeServiceClient - Login successful')

      file_system_client = service_client.get_file_system_client(file_system=configuration['container_name'])

      file_client = file_system_client.get_file_client("/" + file_name)
      
      downloaded_bytes = file_client.read_file()

      log(f, "[RETRIEVE] File '{}' : Length - {}".format(file_name, len(downloaded_bytes)))

      f.close()

      return send_file(io.BytesIO(downloaded_bytes), attachment_filename=file_name, mimetype='image/png')

   except Exception as e:
      log(f, str(e))
      f.close()
      output.append({
         "status" : 'fail',
         "error" : str(e)
      })
      
      return json.dumps(output, sort_keys=True),

@app.route("/process", methods=["GET"])
def process():
   output = []
   
   configuration = get_configuration()

   f = open(configuration['debug_file'], 'a')
   try:
      file_name = request.values.get('filename')

      log(f, "[PROCESS] Account Name: '{}'".format(configuration['account_name']))
      log(f, "[PROCESS] Account Key: '{}'".format(configuration['account_key']))
      log(f, "[PROCESS] Container: '{}'".format(configuration['container_name']))
      log(f, "[PROCESS] File Name: '{}'".format(file_name))
   
      service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format("https", configuration['account_name']), credential=configuration['account_key'])

      log(f, '[PROCESS] DataLakeServiceClient - Login successful')

      file_system_client = service_client.get_file_system_client(file_system=configuration['container_name'])

      file_client = file_system_client.get_file_client("/" + file_name)
      
      downloaded_bytes = file_client.read_file()

      log(f, "[PROCESS] (DECODE) File '{}' : Length - {}".format(file_name, len(downloaded_bytes)))
      
      image_stream = io.BytesIO(downloaded_bytes)
      image_stream.seek(0)
      file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)

      image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

      log(f, "[PROCESS] (DECODED) File '{}' - Image".format(file_name))
      
      b,g,r = cv2.split(image)           # get b,g,r
      rgb_img = cv2.merge([r,g,b])     # switch it to rgb

      dst = cv2.fastNlMeansDenoisingColored(image, None,10,10,7,21)

      log(f, "[PROCESS] (DEONISINED) File '{}'".format(file_name))

      b,g,r = cv2.split(dst)           # get b,g,r
      rgb_dst = cv2.merge([r,g,b])     # switch it to rgb
      
      gray_smooth = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

      log(f, "[PROCESS] (GRAY SCALE)  File '{}'".format(file_name))
      
      gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 
      laplacian = cv2.Laplacian(gray, cv2.CV_64F)
      sobelx = cv2.Sobel(gray,cv2.CV_64F,1,0,ksize=5)
      sobely = cv2.Sobel(gray,cv2.CV_64F,0,1,ksize=5)
 
      edges = cv2.Canny(gray, 100, 200)

      grid = gridspec.GridSpec(2, 5)

      figure = Figure(figsize=(14, 8), tight_layout=True)
      
      log(f, "[PROCESS] (CREATED FIGURE)  File '{}'".format(file_name))

      ax = figure.add_subplot(grid[0, 0])
      ax.imshow(rgb_img)
      
      ax = figure.add_subplot(grid[0, 1])
      ax.imshow(rgb_dst)
      
      ax = figure.add_subplot(grid[0, 2])
      ax.imshow(gray_smooth, cmap = 'gray')  
      
      ax = figure.add_subplot(grid[0, 3])
      ax.imshow(sobely, cmap = 'gray')  
      
      
      ax = figure.add_subplot(grid[0, 4])
      ax.imshow(edges, cmap = 'gray') 

      hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
      
      ax = figure.add_subplot(grid[1, :])
      ax.set_xlabel("Bins")
      ax.set_ylabel("# of Pixels")
      ax.plot(hist)

      buf = io.BytesIO()
      log(f, "[PROCESS] (BEFORE SAVE)  File '{}'".format(file_name))

      figure.savefig(buf, format='png')

      log(f, "[PROCESS] (AFTER SAVE)  File '{}'".format(file_name))

      buf.seek(0)

      log(f, "[PROCESS] File (COMPLETE) '{}'".format(file_name))

      f.close()

      return send_file(buf, attachment_filename='process.png', mimetype='image/png')

   except Exception as e:
      log(f, str(e))
      f.close()
      output.append({
         "status" : 'fail',
         "error" : str(e)
      })
      
      return json.dumps(output, sort_keys=True), 500

@app.route("/upload", methods=["POST"])
def upload():
   configuration = get_configuration()

   file_name = request.values.get('filename')
   chunk = request.values.get('chunk')
   position = request.values.get('position')

   f = open(configuration['debug_file'], 'a')

   output = []

   try: 
      uploadedFiles = request.files
      
      fileContent = None

      for uploadFile in uploadedFiles:
         fileContent = request.files.get(uploadFile)

      global service_client

      log(f, "[UPLOAD] Account Name: '{}'".format(configuration['account_name']))
      log(f, "[UPLOAD] Account Key: '{}'".format(configuration['account_key']))
      log(f, "[UPLOAD] Container: '{}'".format(configuration['container_name']))
      log(f, "[UPLOAD] File Name: '{}'".format(file_name))
      log(f, "[UPLOAD] Chunk: '{}'".format(chunk))
      log(f, "[UPLOAD] Position: '{}'".format(position))

      fileContent = None

      for uploadFile in uploadedFiles:
         fileContent = request.files.get(uploadFile)

      buffer = fileContent.read()

      log(f, '[UPLOAD] Read File Content - ' + str(len(buffer)))

      service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format("https", configuration['account_name']), credential=configuration['account_key'])

      log(f, '[UPLOAD] DataLakeServiceClient - Login successful')

      file_system_client = service_client.get_file_system_client(file_system=configuration['container_name'])
      
      log(f, '[UPLOAD] File System - Login successful')

      file_client = None

      if (int(chunk) == 0):
         file_client = file_system_client.create_file("/" + file_name)
      else:
         file_client = file_system_client.get_file_client("/" + file_name)
      
      file_client.append_data(buffer, int(position), len(buffer))

      output.append({
         "file_name" : file_name,
         "chunk": chunk,
         "status": "OK"
      })

      f.close()
      
      return json.dumps(output, sort_keys=True)

   except Exception as e:
      log(f, str(e))
      f.close()
      output.append({
         "status" : 'fail',
         "error" : str(e)
      })
      
      return json.dumps(output, sort_keys=True), 500

@app.route("/commit", methods=["GET"])
def commit():
   configuration = get_configuration()

   f = open(configuration['debug_file'], 'a')

   try: 
  
      file_name = request.values.get('filename')
      file_length = request.values.get('filelength')

      log(f, "[COMMIT] Account Name: '{}'".format(configuration['account_name']))
      log(f, "[COMMIT] Account Key: '{}'".format(configuration['account_key']))
      log(f, "[COMMIT] Container: '{}'".format(configuration['container_name']))
      log(f, "[COMMIT] File Name: '{}'".format(file_name))
      log(f, "[COMMIT] Length: '{}'".format(file_length))

      service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format("https", configuration['account_name']), credential=configuration['account_key'])

      log(f, '[COMMIT] DataLakeServiceClient - Login successful')

      file_system_client = service_client.get_file_system_client(file_system=configuration['container_name'])

      file_client = file_system_client.get_file_client("/" + file_name)

      file_client.flush_data(int(file_length))

      output = []

      output.append({
         "file_name" : file_name,
         "status": "OK"
      })

      f.close()
      
      return json.dumps(output, sort_keys=True)
   except Exception as e:
      log(f, str(e))
      f.close()
      output.append({
         "status" : 'fail',
         "error" : str(e)
      })
      
      return json.dumps(output, sort_keys=True), 500
@app.route("/")
def start():
    return render_template("main.html")

if __name__ == "__main__":
    PORT = int(environ.get('PORT', '8080'))
    app.run(host='0.0.0.0', port=PORT)