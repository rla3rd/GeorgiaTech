import numpy as np
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import TensorDataset, Dataset
import math
from PIL import Image

def splitdata(df):
    df_train,df_test = train_test_split(df, test_size=0.2, random_state=1)
    df_train, df_val = train_test_split(df_train, test_size=0.25, random_state=1) # 0.25 x 0.8 = 0.2
    return df_train, df_val, df_test

def gettensordata(mydf):
    mydf['y'] = mydf['y'].apply(lambda x: x-1)
    features = [col for col in list(mydf) if 'X_' in col]
    data = np.array(mydf[features])
    target = np.array(mydf['y'])
    dataset = TensorDataset(torch.from_numpy(data.astype('float32')).unsqueeze(1), torch.from_numpy(target).long())
    return dataset

def getoutputsize(inputsize,f, stride):
    newsize = (inputsize-f)/stride + 1
    return math.floor(newsize)

def getshape(imagepath):
    np_im = Image.open(imagepath)
    np_im = np.array(np_im)
    return np_im.shape

def getoutputsize2D(inputsize,f, stride):
    return (getoutputsize(inputsize[0],f,stride),getoutputsize(inputsize[1],f,stride))

def convertrgba(sourcepath, destpath):
    myimage = Image.open(sourcepath)
    myimage = myimage.convert('RGB')
    myimage.save(destpath)
