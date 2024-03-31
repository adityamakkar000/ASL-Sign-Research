import sys
sys.path.append('C:/Users/vinod/Desktop/Aditya Things/fullstack stuff/ASL-Sign-Research/structures')

from models.encoder import Encoder
import os
import numpy as np
import torch
import torch.nn as nn
import pandas
import torch.nn.functional as F
import time
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix
from torcheval.metrics.functional import multiclass_f1_score

print(os.getcwd())

# !pip install torcheval

# hyper parameters
batch_size = 32
epochs = 100000
learning_rate = 1e-4
time_steps = 10
n_emb = 5
classes=10

#encoder layer
data = pandas.read_csv('./data/Data.csv')
#prepare classes
y = data['word']
stoi  = {s:i for i,s in enumerate(sorted(set(y)))}
encode = lambda s: stoi[s]
y = torch.tensor([encode(s) for i,s in enumerate(y)])
# y = F.one_hot((y.view(y.shape[0], 1)),10) # don't use one hot with cross entropy loss

#prepare data
x = torch.tensor(data.iloc[:,2:time_steps*n_emb + 2].to_numpy())
x = torch.nan_to_num(x).float()
x = x.view(x.shape[0], -1, n_emb)
# print(x.dtype, " ", y.dtype)
# print(x.shape)

params = {
  'layers': 10,
  'number_heads': 5,
  'input_size': 10,
  'hidden_size': 5,
  'time_steps': 10,
  'dropout': 0.2
}
model = Encoder(**params)
model.info(layers=False)

splits = 5
kfold = StratifiedKFold(n_splits=splits, shuffle=True, random_state=1337)

for i, (train, test) in enumerate(kfold.split(x,y)):
  Xtr,Ytr = x[train], y[train]
  Xval, Yval = x[test], y[test]
  model = Encoder(**params)
  def get_batches(split):
    x_values, y_values = {
        'train': [Xtr, Ytr],
        'test': [Xval, Yval]
    }[split]
    idx = torch.randint(0, x_values.shape[0], (batch_size,))
    return x_values[idx], y_values[idx]

  def get_accuracy(cm):
    TP = np.diag(cm)
    TN = np.sum(np.sum(cm,axis=0))-(np.sum(cm, axis = 0) + np.sum(cm, axis=1) - np.diag(cm))
    FP = np.sum(cm, axis = 0) - np.diag(cm)
    FN = np.sum(cm, axis=1) - np.diag(cm)

    acc = (TP + TN)/(TP + TN + FP + FN)
    return acc

  @torch.no_grad()
  def get_val_stats(x_val, y_val):
    model.eval()
    logits, val_loss = model(x_val, y_val)
    cm = confusion_matrix(y_val,
                          logits.argmax(axis=1).numpy(), labels=np.arange(10).tolist())
    val_f1 = multiclass_f1_score(logits, y_val,num_classes=classes, average=None)
    accuracy = get_accuracy(cm)
    model.train()
    return val_loss.item(), val_f1, cm, accuracy

  optim = torch.optim.AdamW(model.parameters(), lr=learning_rate)
  start_time = time.time()
  for _ in range(epochs):
    x_epoch, y_epoch = get_batches('train')
    logits, loss = model(x_epoch, y_epoch)
    optim.zero_grad(set_to_none=True)
    loss.backward()
    optim.step()
    if(_ % 500 == 0):
      end_time = time.time()
      delta_time = end_time - start_time
      val_loss, val_f1, cm, accuracy= get_val_stats(Xval, Yval)
      print(f"epoch {_:<4}   Training Loss {loss.item():.4f}   Val loss {val_loss:.4f}   Val F-1 {val_f1.mean().item():.4f}   Accuracy {torch.tensor(accuracy).mean().item():.4f}   Time {delta_time:.1f}")


      start_time = time.time()
