# -*- coding: utf-8 -*-
"""Custom Model

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1KrVkttbjEq4IidD5OQ94cRevyFYWj51o
"""

from google.colab import drive
drive.mount('/content/drive', force_remount=True)

!pip install keras

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

import os
from PIL import Image

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten, LSTM, GRU, Lambda, Input, MaxPooling2D, Dropout, Activation, BatchNormalization, AveragePooling2D
from tensorflow.keras import Model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.regularizers import l1_l2
import tensorflow as tf
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import load_model
from tensorflow.keras import layers

from tensorflow.keras.preprocessing.image import ImageDataGenerator

input_layer = Input((256, 256, 3))

model = Conv2D(128, kernel_size=3, strides = (2,2), kernel_regularizer=l1_l2(0.01), bias_regularizer=l1_l2(0.01))(input_layer)
model = BatchNormalization()(model)
model = Activation('relu')(model)
model = MaxPooling2D(pool_size = (3, 3))(model)

model = Conv2D(64, kernel_size=3, strides = (2,2), kernel_regularizer=l1_l2(0.01), bias_regularizer=l1_l2(0.01))(model)
model = BatchNormalization()(model)
model = Activation('relu')(model)
model = MaxPooling2D(pool_size = (3, 3))(model)

model = Flatten()(model)
model = Dropout(0.1)(model)
model = tf.expand_dims(model, axis=-1)
model = LSTM(20, return_sequences=True, kernel_regularizer=l1_l2(0.01), bias_regularizer=l1_l2(0.01))(model)
model = Activation('relu')(model)
model = LSTM(10, return_sequences=True, kernel_regularizer=l1_l2(0.01), bias_regularizer=l1_l2(0.01))(model)
model = Activation('relu')(model)
model = Flatten()(model)
model = Dense(1)(model)
model = Activation('sigmoid')(model)

full_model = Model(input_layer, model)
full_model.summary()

gens = []
ppl = 26

pathv = '/content/drive/MyDrive/Graph_CNN_Project/VG_Dataset'

for i in range(ppl):
  imgdatagen = ImageDataGenerator(rescale=1./255)
  imgdatagen = imgdatagen.flow_from_directory(
    pathv+'/Person'+str(i+1),
    batch_size=300,
    class_mode='binary'
  )
  gens.append(imgdatagen)


X, y = [], []

for i in range(ppl):
  images, labels = gens[i].next()
  for im in images:
    X.append(im)
  for lbl in labels:
    y.append(lbl)
  print("Person " + str(i+1) + " done!")

X = np.array(X)
y = np.array(y)

X.shape, y.shape

opt = SGD(learning_rate = 0.0005)
full_model.compile(optimizer = opt , loss = 'binary_crossentropy', metrics = ['accuracy'])

def get_data_for_ith_person(person):
  st, ed = person*300, (person+1)*300
  x_sub, x_rest = X[st:ed], np.concatenate((X[:st], X[ed:]))
  y_sub, y_rest = y[st:ed], np.concatenate((y[:st], y[ed:]))

  return x_sub, y_sub, x_rest, y_rest

histories = []

# keep changing this for every person - DO NOT DO IN LOOPS
person = 25

x_sub, y_sub, x_rest, y_rest = get_data_for_ith_person(person)
hist = full_model.fit(x_rest, y_rest, batch_size = 15, validation_data=(x_sub, y_sub), shuffle = True, epochs=10)
histories.append(hist)

pwd

cd /content/drive/MyDrive/Graph_CNN_Custom_Model/Person1

cd ..

full_model.save("sscv_rkt_person1.h5")

