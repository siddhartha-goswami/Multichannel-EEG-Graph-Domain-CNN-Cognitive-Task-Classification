# -*- coding: utf-8 -*-
"""VisibilityGraphDataset

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1EMXzgumJGQ8Q90YO_kZxT4bHEiX-_Rv-
"""

!pip install ts2vg

import os
import numpy as np
from os.path import basename

from scipy.io import loadmat
from scipy.signal import savgol_filter

from pandas import read_csv
from pandas import DataFrame
from pandas import Grouper

import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import matplotlib.cm as cm

import pywt

from ts2vg import HorizontalVG
from ts2vg import NaturalVG
import networkx as nx

from scipy.linalg import fractional_matrix_power

from google.colab import drive
drive.mount('/content/drive', force_remount=True)

def waveletdecompose(kk):
  X = kk
  coeffs = pywt.wavedec(kk, 'db4',level=5);
  xa= wrcoef(X,'d',coeffs,'db4',5);
  xd1= wrcoef(X,'d',coeffs,'db4',5);
  xd2= wrcoef(X,'d',coeffs,'db4',4);
  xd3= wrcoef(X,'d',coeffs,'db4',3);
  xd4= wrcoef(X,'d',coeffs,'db4',2);
  xd5= wrcoef(X,'d',coeffs,'db4',1);
  return [xa, xd1, xd2, xd3, xd4, xd5]

def ocular_artifact_elimination(x1):
  x1=x1-x1.mean();
  x1=x1/max(abs(x1));
  [xa, xd1, xd2, xd3, xd4, xd5]=waveletdecompose(x1)
  order=2;
  window=21;
  xaf = savgol_filter(xa,window,order)
  kk=xa-xaf;
  xfn=kk+xd1+xd2+xd3+xd4+xd5
  xfnH=np.matrix(xfn).getH()
  return xfnH

def wrcoef(X, coef_type, coeffs, wavename, level):
    N = np.array(X).size
    a, ds = coeffs[0], list(reversed(coeffs[1:]))

    if coef_type == 'd':
        return pywt.upcoef('d', ds[level-1], wavename, level=level)[:N]
    else:
        raise ValueError("Invalid coefficient type: {}".format(coef_type))

def read_cnt(path):
    '''
        clab: channel label
        fs: sampling rate (200)
        title: 'wg'
        x: signal len (2 tasks) * 5 (# channels)  (371283, 5)
        T: # samples per task
        yUnit: uV
    '''
    file_name = basename(path)
    file_name = file_name[0:len(file_name)-4]
    data = loadmat(path)[file_name]
    clab = data[0, 0]['clab'][0]#.astype('str')
    clab = [clab[i][0] for i in range(len(clab))]
    fs = data[0, 0]['fs'][0][0]
    title = data[0, 0]['title'][0]
    x = data[0, 0]['x']
    T = data[0, 0]['T'][0][0]
    yUnit = data[0, 0]['yUnit'][0]
    #return clab, fs, title, x, T, yUnit
    return x

def read_mrk(path):
    '''
        time: defines the time points of event in msec
        y: class labels (one hot)
        className: ['WG', 'BL']
        event: len = 60
            16: WG
            32: BL
    '''
    file_name = basename(path)
    file_name = file_name[0:len(file_name)-4]
    data = loadmat(path)[file_name]

    time = data[0, 0]['time'][0]
    y = data[0, 0]['y']
    className = data[0, 0]['className'][0]
    className = [className[i][0] for i in range(len(className))]
    event = data[0, 0]['event'][0][0][0].reshape(-1)

    #return time, y, className, event
    return time, event, y

#def read_data(dataset_path):
 #   dir_list = os.listdir(dataset_path)
  #  dir_list.sort()
   # x_data = []
    #for directory in dir_list: # process every subject directory
      #  print('directory:',directory)
       # files = os.listdir(os.path.join(dataset_path, directory))
       # for file in files: # process every subject file
       #     path = os.path.join(dataset_path, directory, file)
        #    if(file[0:6] == 'cnt_wg'): # EEG signal (cnt_wg)
          #      x = read_cnt(path)
          #  elif(file[0:6] == 'mrk_wg'): # read label related data, mrk_wg_event = mrk_wg.y
            #    time, event, y = read_mrk(path)
       # x_data.append(process_datasetC(x, time, event))
   # return x_data # people(26) x type (2 tasks) x trials (30)

def read_data_for_1_person(dataset_path, person):
    dir_list = os.listdir(dataset_path)
    dir_list.sort()
    x_data_for_1_person = []
    directory = dir_list[person - 1]
    print('directory:',directory)
    files = os.listdir(os.path.join(dataset_path,directory))
    for file in files: # process every subject file
            path = os.path.join(dataset_path, directory, file)
            if(file[0:6] == 'cnt_wg'): # EEG signal (cnt_wg)
                x = read_cnt(path)
            elif(file[0:6] == 'mrk_wg'): # read label related data, mrk_wg_event = mrk_wg.y
                time, event, y = read_mrk(path)

    x_data_for_1_person.append(process_datasetC(x, time, event))
    return x_data_for_1_person

def process_datasetC(x, time, event):
    print("x shape",x.shape)
    '''
        time is the start time of the event

        event: len = 60
            16: 0-back session (total 30 trials)
            32: 2-back session (total 30 trials)
    '''
    wg_labels = [16, 32]
    x_wg = [[], []] # Seperate list for WG and BL
    for i, wg_label in enumerate(wg_labels):
        print("\nTask",i)
        event_idx = np.where(event == wg_label)[0] # beginning of each task (WG or BL) index
        x_tmp = []
        for idx in event_idx:
            print("VG",idx)
            t_idx = idx # time index

            s_time = time[t_idx]
            if idx + 1 == 60:
                e_time = (x.shape[0] - 1) / 200 * 1000
            else:
                e_time = time[t_idx + 1]

            s_sp_idx = int(np.floor(s_time / 1000 * 200)) # sample point index
            e_sp_idx = int(np.floor(e_time / 1000 * 200)) # sample point index

            # ocular_artifact_elimination(here)

            channellist = []
            for channel in range(5):
              ocelim = (ocular_artifact_elimination(x[s_sp_idx:e_sp_idx,channel])) #channel = 0

              visiblity_graph = NaturalVG(directed=None).build(np.array(ocelim).flatten())
              nx_visiblity_graph = visiblity_graph.as_networkx()
              channellist.append(nx_visiblity_graph)

            x_wg[i].append(channellist)

    return x_wg # python list : 2(task)  x 5 (channels) x 30 (trials for each channel)

pwd

cd '/content/drive/MyDrive/Graph_CNN_Dataset/VG_Dataset'

pwd

def get_graph_and_save_wg(x_wg_bl, person):
    x_wgbl_1_person = x_wg_bl[0] #1 person
    x_wg_data = x_wgbl_1_person[0] #WG data for that person
    x_bl_data = x_wgbl_1_person[1] #BL data for that person

    os.mkdir('./'+'Person'+str(person))

    #WG Graphs
    os.mkdir('./'+'Person'+str(person)+'/'+'WG')
    for trials_wg in range(len(x_wg_data)):
        for channels_wg in range(len(x_wg_data[0])):
            nxg = x_wg_data[trials_wg][channels_wg]

            graph_plot_options = {
            'with_labels': False,
            'node_size': 1,
            'node_color': [(0, 0, 0, 1)],
            'edge_color': [(0, 0, 0, 0.15)],
            }

            ax2 = plt.subplot(111)
            nx.draw(nxg, ax=ax2, **graph_plot_options)
            ax2.figure.savefig('./Person' + str(person) + '/' + 'WG' +'/'+ 'Trial' + str(trials_wg) + 'Channel' + str(channels_wg) +'.png')
            print('Person ' + str(person) + ' WG' + ', Trial ' + str(trials_wg) + ', Channel ' + str(channels_wg) + ' done' )
            plt.close('all')

def get_graph_and_save_bl(x_wg_bl, person):
    x_wgbl_1_person = x_wg_bl[0] #1 person
    x_wg_data = x_wgbl_1_person[0] #WG data for that person
    x_bl_data = x_wgbl_1_person[1] #BL data for that person

    #BL Graphs
    os.mkdir('./'+'Person'+str(person)+'/'+'BL')
    for trials_bl in range(len(x_bl_data)):
        for channels_bl in range(len(x_bl_data[0])):
            nxg = x_bl_data[trials_bl][channels_bl]

            graph_plot_options = {
            'with_labels': False,
            'node_size': 1,
            'node_color': [(0, 0, 0, 1)],
            'edge_color': [(0, 0, 0, 0.15)],
            }

            ax2 = plt.subplot(111)
            nx.draw(nxg, ax=ax2, **graph_plot_options)
            ax2.figure.savefig('./Person' + str(person) + '/' + 'BL' +'/'+ 'Trial' + str(trials_bl) + 'Channel' + str(channels_bl) +'.png')
            print('Person ' + str(person) + ' BL' + ', Trial ' + str(trials_bl) + ', Channel ' + str(channels_bl) + ' done' )
            plt.close('all')

if __name__ == '__main__':

    '''
    28 EEG and 2 EoG channels name
        ['Fp1', 'AFF5h', 'AFz', 'F1', 'FC5',
        'FC1', 'T7', 'C3', 'Cz', 'CP5', 'CP1',
        'P7', 'P3', 'Pz', 'POz', 'O1', 'Fp2',
        'AFF6h', 'F2', 'FC2', 'FC6', 'C4', 'T8',
        'CP2', 'CP6', 'P4', 'P8', 'O2', 'HEOG', 'VEOG']
    '''
    person_no = 11
    x = read_data_for_1_person('{}'.format('/content/drive/MyDrive/Graph_CNN_Dataset/EEG_01-26_MATLAB'), person_no)
    get_graph_and_save_wg(x, person_no)
    #get_graph_and_save_bl(x, person_no)
    print('people:',len(x))
    print('task:',len(x[0]))
    print('no of trials:',len(x[0][0]))
    print('no of channels:',len(x[0][0][0]))

#break

import pandas as pd

print('graph:',(x[0][0][0]))

df = pd.DataFrame(columns = ['Participant','Task','Fp1', 'AFF5h', 'AFz', 'F1', 'FC5'])

for person_index, task_list in enumerate(x):
  for task_type,trial_list in enumerate(task_list):
    for channelno, channel_list in enumerate(trial_list):
        df.loc[len(df)] = {'Participant' : person_index + 1, 'Task' : "WG" if task_type == 0 else "BL", 'Fp1':channel_list[0] , 'AFF5h':channel_list[1], 'AFz':channel_list[2], 'F1':channel_list[3], 'FC5' :channel_list[4]}

df.head()

G1 = df['Fp1'].values[0]
print(G1)

df.shape