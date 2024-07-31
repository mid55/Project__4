from flask import Flask, request, render_template, send_file
from PIL import Image
import numpy as np
import io
import base64
import tensorflow as tf
from tensorflow.keras import layers, models

app = Flask(__name__)


# Create a simple watermark embedding model
def create_watermark_model(input_shape):
    model = models.Sequential([
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model


# Function to encrypt an image using a simple XOR operation
def encrypt_image(image):
    image_array = np.array(image)
    image_array = image_array.astype(np.uint8)
    encrypted_image = np.bitwise_xor(image_array, 255)
    return encrypted_image


# Function to embed a watermark using the trained model
def embed_watermark(original_image, watermark_model):
    encrypted_image = encrypt_image(original_image)
    resized_image = tf.image.resize(encrypted_image, (256, 256))
    original_array = np.array(resized_image)
    original_array = original_array / 255.0
    watermark_prob = watermark_model.predict(np.expand_dims(original_array, axis=0))
    watermark_prediction = (watermark_prob > 0.5).astype(np.uint8) * 255
    watermarked_array = original_array + watermark_prediction / 255.0
    watermarked_array = np.clip(watermarked_array, 0, 1.0)
    watermarked_array *= 255.0
    watermarked_image = Image.fromarray(watermarked_array.astype(np.uint8))
    return watermarked_image


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and file.filename.lower().endswith(('png', 'jpg', 'jpeg')):
        image = Image.open(file)
        input_shape = (256, 256, 3)
        watermark_model = create_watermark_model(input_shape)
        watermarked_image = embed_watermark(image, watermark_model)

        buffered = io.BytesIO()
        watermarked_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return render_template('result.html', image_data=img_str)

    return 'Invalid file format', 400


if __name__ == '__main__':
    app.run(debug=True)
