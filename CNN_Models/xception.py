# -*- coding: utf-8 -*-
"""Xception

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1RmjkBitm363c8A5e5G8FM-2emkho69sI
"""

import tensorflow as tf
import keras
from keras.models import Sequential
from keras.layers import Dense, Conv2D, Flatten
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model

import os
from collections import Counter
from PIL import Image
import numpy as np
import random
import pandas as pd

xceptionmodel = tf.keras.applications.Xception(
    include_top=False,
    weights="imagenet",
    input_tensor=None,
    input_shape=(288, 432, 3),
    pooling="max"
)
xceptionmodel.trainable = False

inputs = keras.Input(shape=(288, 432, 3))

x = xceptionmodel(inputs, training=False)
x = keras.layers.Dense(128, activation="relu")(x)
x = keras.layers.Dense(32, activation="relu")(x)
outputs = keras.layers.Dense(2, activation="softmax")(x)
model = keras.Model(inputs, outputs)

model.summary()

model.compile(optimizer="adam", loss="categorical_crossentropy", metrics="accuracy")
model.save("/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/xceptionmodel")

def get_data_split(person_num):
  direc = '/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset'
  x_train, x_val, y_train, y_val, yy_train, yy_val = [], [], [], [], [], []

  for i in range(26):
    person = "Person"+str(i+1)

    path = direc+'/'+person+'/WG'
    for imfile in os.listdir(path):
      img = Image.open(path+'/'+imfile)
      if i+1 == person_num:
        x_val.append(np.array(img)[:, :, :3])
        yy_val.append(1)
      else:
        x_train.append(np.array(img)[:, :, :3])
        yy_train.append(1)

    path = direc+'/'+person+'/BL'
    for imfile in os.listdir(path):
      img = Image.open(path+'/'+imfile)
      if i+1 == person_num:
        x_val.append(np.array(img)[:, :, :3])
        yy_val.append(0)
      else:
        x_train.append(np.array(img)[:, :, :3])
        yy_train.append(0)

  z = list(zip(x_train, yy_train))
  random.shuffle(z)
  x_train, yy_train = zip(*z)

  z = list(zip(x_val, yy_val))
  random.shuffle(z)
  x_val, yy_val = zip(*z)

  x_train, yy_train = np.array(x_train), np.array(yy_train)
  x_val, yy_val = np.array(x_val), np.array(yy_val)

  y_train = np.zeros((yy_train.size, yy_train.max()+1))
  y_train[np.arange(yy_train.size), yy_train] = 1
  yy_train = None

  y_val = np.zeros((yy_val.size, yy_val.max()+1))
  y_val[np.arange(yy_val.size), yy_val] = 1
  yy_val = None

  return x_train, y_train, x_val, y_val

histories = []

pno = 20
for i in range(pno, pno+1):
  print("Reading data for Person " + str(i+1) + ".......", end=' ')
  x_train, y_train, x_val, y_val = get_data_split(i+1)
  print("Done!")

  my_callback = tf.keras.callbacks.EarlyStopping(
    monitor="accuracy",
    min_delta=0.01,
    patience=2,
    verbose=0,
    mode="auto",
    restore_best_weights=True,
  )

  model = load_model("/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/xceptionmodel")
  history = model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=5, callbacks=[my_callback])

  del(x_train)
  del(y_train)
  del(x_val)
  del(y_val)

  print("Person " + str(i+1) + " done!")

  pd.DataFrame(history.history).to_csv('/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/Person-'+str(i+1)+'.csv')
  model.save("/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/xceptionmodel")

pd.DataFrame(history.history).to_csv('/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/Person-2.csv')
model.save("/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset/xceptionmodel")

