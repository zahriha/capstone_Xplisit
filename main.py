import requests
import json
import base64
from google.cloud import storage
import numpy as np
from keras.preprocessing import image
import keras.models
from keras.models import model_from_json



# create remote client to bucket
storage_client = storage.Client()
bucket = storage_client.get_bucket('model-bucket-nails')

# download model.json and model.h5 to local machine
blob = bucket.blob('model/model.json')
blob.download_to_filename('/tmp/model.json')
blob2 = bucket.blob('model/model.h5')
blob2.download_to_filename('/tmp/model.h5')

# get model from model.json
json_file = open('/tmp/model.json', 'r')
model_json = json_file.read()
json_file.close()
model = model_from_json(model_json)

# load weights from model.h5 from bucket into new model
model.load_weights("/tmp/model.h5")
print("Load weights into new model")

# compile and evaluate model
model.compile(loss = 'categorical_crossentropy', 
              optimizer='rmsprop', 
              metrics=['accuracy'])

# function to predict
def make_prediction(request):
    if request.method == 'GET':
        return "Just try send POST request"
    elif request.method == 'POST':
        # get data from request
        img_data = request.get_json()
        print("Data image from request:")
        print(img_data)

        # get data keys
        for i in img_data.keys():
            filename = i
        print(filename)

        # encode utf-8 string to base64
        img_val = img_data[filename].encode('utf-8')
        print("Image value in Base64:")
        print(img_val)

        # decode base64 to bytes
        img_val_to_bytes = base64.decodebytes(img_val)
        print("Image value in bytes:")
        print(img_val_to_bytes)

        # change img_data values
        img_data[filename] = img_val_to_bytes
        print("Fixed Image Data")
        print(img_data)

        # create image from bytes
        with open('/tmp/'+filename, 'wb') as f:
            f.write(img_val_to_bytes)

        CATEGORIES = ["aloperia areata", "beau's lines", "bluish nail", "clubbing", "darier's disease", "eczema", "koilonychia", "leukonychia", "lindsay's nails", "muehrck-e's lines", "normal", "onycholycis", "pale nail", "red lunula", "splinter hemmorrage", "terry's nail", "white nail", "yellow nails"]

        # make prediction
        print("Make prediction:")
        path = '/tmp/'+filename
        img = image.load_img(path, target_size=(150, 150))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)

        images = np.vstack([x])
        prediction = model.predict(images, batch_size=10)

        print(path)
        print(str(prediction))

        # get disease name and percentage
        res = "{} | {:2.0f}%".format(CATEGORIES[np.argmax(prediction)], 100*np.max(prediction))

        res = res.split(' | ')
        name = res[0]
        percent = res[1]

        data = {}
        
        # check for unhealthy nails
        if name != 'normal':
            # get the details from bucket
            blob3 = bucket.blob('data/'+ name + '.txt')
            details = blob3.download_as_string()
            details = details.decode('utf-8')
            details = details.split(';;')

            data['name'] = details[0]
            data['percent'] = percent
            data['desc'] = details[1]
            data['treat'] = details[2]
        
        # check for healthy nails
        elif name == 'normal':
            data['name'] = name

        return str(data)        