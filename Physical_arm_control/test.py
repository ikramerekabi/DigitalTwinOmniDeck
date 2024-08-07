from tensorflow.keras.layers.experimental.preprocessing import StringLookup
from tensorflow import keras
import matplotlib.pyplot as plt
import tensorflow as tf
import numpy as np
import os
from PIL import Image

np.random.seed(42)
tf.random.set_seed(42)


filenames_img = sorted(os.listdir('/home/g9/Downloads/Dataset/Total Images'))
filenames_gt = sorted(os.listdir('/home/g9/Downloads/Dataset/Total GT'))
filenames_imgsplit = [filename.replace('.jpg', '') for filename in filenames_img]
filenames_gtsplit = [filename.replace('.txt', '') for filename in filenames_gt]
print(len(filenames_imgsplit))
print(len(filenames_gtsplit))

split_idx = int(0.8 * len(filenames_imgsplit))
train_samples = filenames_img[:split_idx]
train_samples_split = filenames_imgsplit[:split_idx]
test_samples = filenames_img[split_idx:]
test_samples_split = filenames_imgsplit[split_idx:]

val_split_idx = int(0.5 * len(test_samples))
validation_samples = test_samples[:val_split_idx]
validation_samples_split = test_samples_split[:val_split_idx]
test_samples = test_samples[val_split_idx:]
test_samples_split = test_samples_split[val_split_idx:]

assert len(filenames_imgsplit) == len(train_samples) + len(validation_samples) + len(test_samples)

print(f"Total training samples: {len(train_samples)}")
print(f"Total validation samples: {len(validation_samples)}")
print(f"Total test samples: {len(test_samples)}")
print(f' Example from training dataset {train_samples_split[0]}')

base_path = '/home/g9/Downloads/Dataset/'
base_image_path = os.path.join(base_path, "Total Images/")
base_GT_path = os.path.join(base_path, "Total GT/")

def get_image_paths_and_labels(filenames_img, filenames_imgsplit):
    paths = []
    labels = []
    for i in range(len(filenames_imgsplit)):
        img_path = os.path.join(base_image_path, filenames_img[i])
        if os.path.getsize(img_path):
            paths.append(img_path)
            label_path = os.path.join(base_GT_path, filenames_imgsplit[i].replace('.tif', '') + '.txt')
            try:
                with open(label_path, "r") as label_file:
                    labels.append(label_file.read())
                print(f"File found and read successfully: {label_path}")
            except FileNotFoundError:
                print(f"Warning: File not found - {label_path}")
                paths.pop()
        else:
            print(f"Warning: Image file not found or is empty - {img_path}")
    return paths, labels

train_img_paths, train_labels = get_image_paths_and_labels(train_samples, train_samples_split)
validation_img_paths, validation_labels = get_image_paths_and_labels(validation_samples, validation_samples_split)
test_img_paths, test_labels = get_image_paths_and_labels(test_samples, test_samples_split)

train_labels_cleaned = []
characters = set()
max_len = 0

for label in train_labels:
    label = label.split(" ")[-1].strip()
    for char in label:
        characters.add(char)
    max_len = max(max_len, len(label))
    train_labels_cleaned.append(label)

print("Maximum length: ", max_len)
print("Vocab size: ", len(characters))

train_labels_cleaned[:10]

def clean_labels(labels):
    cleaned_labels = []
    for label in labels:
        label = label.split(" ")[-1].strip()
        cleaned_labels.append(label)
    return cleaned_labels

validation_labels_cleaned = clean_labels(validation_labels)
test_labels_cleaned = clean_labels(test_labels)

AUTOTUNE = tf.data.AUTOTUNE
char_to_num = StringLookup(vocabulary=list(characters), mask_token=None)
num_to_char = StringLookup(vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True)

def distortion_free_resize(image, img_size):
    w, h = img_size
    image = tf.image.resize(image, size=(h, w), preserve_aspect_ratio=True)
    pad_height = h - tf.shape(image)[0]
    pad_width = w - tf.shape(image)[1]
    if pad_height % 2 != 0:
        height = pad_height // 2
        pad_height_top = height + 1
        pad_height_bottom = height
    else:
        pad_height_top = pad_height_bottom = pad_height // 2
    if pad_width % 2 != 0:
        width = pad_width // 2
        pad_width_left = width + 1
        pad_width_right = width
    else:
        pad_width_left = pad_width_right = pad_width // 2
    image = tf.pad(image, paddings=[[pad_height_top, pad_height_bottom], [pad_width_left, pad_width_right], [0, 0]])
    image = tf.transpose(image, perm=[1, 0, 2])
    image = tf.image.flip_left_right(image)
    return image

batch_size = 64
padding_token = 99
image_width = 64
image_height = 32

def preprocess_image(image_path, img_size=(image_width, image_height)):
    try:
        image_path = image_path
        image = Image.open(image_path)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image = image.resize(img_size)
        image = np.array(image)
        image = tf.cast(image, tf.float32) / 255.0  
        return image
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return tf.zeros([image_height, image_width, 3])

def vectorize_label(label):
    label = char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
    length = tf.shape(label)[0]
    pad_amount = max_len - length
    label = tf.pad(label, paddings=[[0, pad_amount]], constant_values=padding_token)
    return label

label = vectorize_label(train_labels_cleaned[0])
indices = tf.gather(label, tf.where(tf.math.not_equal(label, padding_token)))
label = tf.strings.reduce_join(num_to_char(indices))
label = label.numpy().decode("utf-8")
print(label)

def process_images_labels(image_path):
    image = tf.py_function(func=preprocess_image, inp=[image_path], Tout=tf.float32)
    # label = vectorize_label(label)
    return image

def prepare_dataset(image_paths):
    dataset = tf.data.Dataset.from_tensor_slices(image_paths).map(process_images_labels, num_parallel_calls=AUTOTUNE)
    return dataset.batch(batch_size).cache().prefetch(AUTOTUNE)

train_ds = prepare_dataset(train_img_paths)

processed_images = []
for image in train_img_paths:
    im = preprocess_image(image)
    # im = tf.py_function(func=preprocess_image, inp=[image], Tout=tf.float32)
    processed_images.append(im)

# validation_ds = prepare_dataset(validation_img_paths, validation_labels_cleaned)
# test_ds = prepare_dataset(test_img_paths, test_labels_cleaned)

# try:
#     for data in train_ds.take(2):
#         images, labels = data["image"], data["label"]
#         _, ax = plt.subplots(4, 4, figsize=(15, 8))
#         for i in range(16):
#             img = images[i]
#             img = tf.image.flip_left_right(img)
#             img = tf.transpose(img, perm=[1, 0, 2])
#             img = (img * 255.0).numpy().clip(0, 255).astype(np.uint8)
#             img = img[:, :, 0]
#             label = labels[i]
#             indices = tf.gather(label, tf.where(tf.math.not_equal(label, padding_token)))
#             label = tf.strings.reduce_join(num_to_char(indices))
#             label = label.numpy().decode("utf-8")
#             ax[i // 4, i % 4].imshow(img, cmap="gray")
#             ax[i // 4, i % 4].set_title(label[::-1])
#             ax[i // 4, i % 4].axis("off")
#     plt.show()
# except:
#     print("Exception")

# class CTCLayer(keras.layers.Layer):
#     def __init__(self, name=None):
#         super().__init__(name=name)
#         self.loss_fn = keras.backend.ctc_batch_cost

#     def call(self, y_true, y_pred):
#         batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
#         input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
#         label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")
#         input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
#         label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")
#         print(input_length, "----", label_length)
#         loss = self.loss_fn(y_true, y_pred, input_length, label_length)
#         self.add_loss(loss)
#         return y_pred

def loss_func(y_true, y_pred):
    batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
    input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
    label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")
    input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
    label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")
    # print(input_length, "----", label_length)
    loss = keras.backend.ctc_batch_cost(y_true, y_pred, input_length, label_length)
    return loss

def build_model():
    input_img = keras.Input(shape=(image_width, image_height, 1), name="image")
    x = keras.layers.Conv2D(32, (3, 3), activation="relu", kernel_initializer="he_normal", padding="same", name="Conv1")(input_img)
    x = keras.layers.MaxPooling2D((2, 2), name="pool1")(x)
    x = keras.layers.BatchNormalization()(x)
    new_shape = ((image_width // 2), (image_height // 2) * 32)
    x = keras.layers.Reshape(target_shape=new_shape, name="reshape")(x)
    x = keras.layers.Dense(16, activation="relu", name="dense2")(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Bidirectional(keras.layers.LSTM(128, return_sequences=True, dropout=0.35))(x)
    x = keras.layers.Dense(len(char_to_num.get_vocabulary()) + 2, activation="softmax", name="dense3")(x)
    # labels = keras.layers.Input(name="label", shape=(None,))
    # output = CTCLayer(name="ctc_loss")(labels, x)
    model = keras.models.Model(inputs=input_img, outputs=x, name="handwriting_recognizer",)
    lr_schedule = keras.optimizers.schedules.ExponentialDecay(initial_learning_rate=0.0001, decay_steps=10000, decay_rate=0.9)
    opt = keras.optimizers.Adam(learning_rate=lr_schedule)
    model.compile(optimizer=opt, loss=loss_func)
    return model

model = build_model()
model.summary()

# validation_images = []
# validation_labels = []
# for batch in validation_ds:
#     validation_images.append(batch["image"])
#     validation_labels.append(batch["label"])

# def calculate_edit_distance(labels, predictions):
#     saprse_labels = tf.sparse.from_dense(labels)
#     input_len = np.ones(predictions.shape[0]) * predictions.shape[1]
#     predictions_decoded = keras.backend.ctc_decode(predictions, input_length=input_len, greedy=False, beam_width=100,)[0][0][:, :max_len]
#     sparse_predictions = tf.sparse.from_dense(predictions_decoded)
#     edit_distances = tf.edit_distance(sparse_predictions, saprse_labels, normalize=False)
#     return tf.reduce_mean(edit_distances)

class EditDistanceCallback(keras.callbacks.Callback):
    def __init__(self, pred_model):
        super().__init__()
        self.prediction_model = pred_model

    def on_epoch_end(self, epoch, logs=None):
        edit_distances = []
        for i in range(len(validation_images)):
            labels = validation_labels[i]
            predictions = self.prediction_model.predict(validation_images[i])
            edit_distances.append(calculate_edit_distance(labels, predictions).numpy())
        print(f"Mean edit distance for epoch {epoch + 1}: {np.mean(edit_distances):.4f}")

epochs = 20
model = build_model()
prediction_model = keras.models.Model(model.get_layer(name="image").input, model.get_layer(name="dense3").output)
# edit_distance_callback = EditDistanceCallback(prediction_model)
stopping = tf.keras.callbacks.EarlyStopping(monitor="val_loss", min_delta=0, patience=3, verbose=0, mode="auto", baseline=None, restore_best_weights=False)
history = model.fit(processed_images, train_labels_cleaned, epochs=epochs, shuffle=True)

def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :max_len]
    output_text = []
    for res in results:
        res = tf.gather(res, tf.where(tf.math.not_equal(res, -1)))
        res = tf.strings.reduce_join(num_to_char(res)).numpy().decode("utf-8")
        output_text.append(res)
    return output_text

for batch in test_ds.take(1):
    batch_images = batch["image"]
    _, ax = plt.subplots(4, 4, figsize=(20, 8))
    preds = prediction_model.predict(batch_images)
    pred_texts = decode_batch_predictions(preds)
    for i in range(16):
        img = batch_images[i]
        img = tf.image.flip_left_right(img)
        img = tf.transpose(img, perm=[1, 0, 2])
        img = (img * 255.0).numpy().clip(0, 255).astype(np.uint8)
        img = img[:, :, 0]
        title = f"Prediction: {pred_texts[i]}"
        ax[i // 4, i % 4].imshow(img, cmap="gray")
        ax[i // 4, i % 4].set_title(title)
        ax[i // 4, i % 4].axis("off")
plt.show()
