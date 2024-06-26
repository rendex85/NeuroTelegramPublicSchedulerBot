import io

import tensorflow as tf
import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing.image import load_img
from tensorflow.keras.preprocessing.image import img_to_array


def predict(img_bytes, model):
    img = Image.open(io.BytesIO(img_bytes))
    img = img.convert('RGB')
    img = img.resize((224, 224))
    image = img_to_array(img)
    image = np.expand_dims(image, axis=0)
    images = np.vstack([image])

    prediction = model.predict(images)
    # print("----------------",prediction)
    if prediction[0][0] > 0.8:
        return "meme"
    else:
        return "anime"
