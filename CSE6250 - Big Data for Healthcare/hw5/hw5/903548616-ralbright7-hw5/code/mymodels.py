import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
import numpy as np

##### DO NOT MODIFY OR REMOVE THIS VALUE #####
checksum = '169a9820bbc999009327026c9d76bcf1'
##### DO NOT MODIFY OR REMOVE THIS VALUE #####


class MyMLP2(nn.Module):
	def __init__(self):
		super(MyMLP2, self).__init__()
		self.hidden = nn.Linear(178, 16)
		self.output = nn.Linear(16, 5)
		self.sigmoid = nn.Sigmoid()
		
	def forward(self, x):
		x = F.relu(self.hidden(x))
		x = self.output(x)
		x = self.sigmoid(x)
		return x


class MyMLP(nn.Module):
	def __init__(self):
		super(MyMLP, self).__init__()
		self.hidden1 = nn.Linear(178, 89)
		self.hidden2 = nn.Linear(89, 44)
		self.hidden3 = nn.Linear(44, 22)
		self.hidden4 = nn.Linear(22, 10)
		self.output = nn.Linear(10, 5)
		self.sigmoid = nn.Sigmoid()
		
	def forward(self, x):
		x = F.relu(self.hidden1(x))
		x = F.relu(self.hidden2(x))
		x = F.relu(self.hidden3(x))
		x = F.relu(self.hidden4(x))
		x = self.output(x)
		x = self.sigmoid(x)
		return x


class MyCNN2(nn.Module):
	def __init__(self):
		super(MyCNN2, self).__init__()
		self.conv1 = nn.Conv1d(in_channels=1, out_channels=6, kernel_size=5)
		self.pool = nn.MaxPool1d(kernel_size=2)
		self.conv2 = nn.Conv1d(6, 16, 5)
		self.fc1 = nn.Linear(in_features=16 * 41, out_features=128)
		self.fc2 = nn.Linear(128, 5)

	def forward(self, x):
		x = self.pool(F.relu(self.conv1(x)))
		x = self.pool(F.relu(self.conv2(x)))
		x = x.view(-1, 16 * 41)
		x = F.relu(self.fc1(x))
		x = self.fc2(x)
		return x


class MyCNN(nn.Module):
	def __init__(self):
		super(MyCNN, self).__init__()
		self.conv1 = nn.Conv1d(in_channels=1, out_channels=6, kernel_size=5)
		self.pool = nn.MaxPool1d(kernel_size=2)
		self.conv2 = nn.Conv1d(6, 16, 5)
		self.fc1 = nn.Linear(in_features=16 * 41, out_features=512)
		self.fc2 = nn.Linear(512, 256)
		self.fc3 = nn.Linear(256, 128)
		self.fc4 = nn.Linear(128, 64)
		self.fc5 = nn.Linear(64, 5) 

	def forward(self, x):
		x = self.pool(F.relu(self.conv1(x)))
		x = self.pool(F.relu(self.conv2(x)))
		x = x.view(-1, 16 * 41)
		x = F.relu(self.fc1(x))
		x = F.relu(self.fc2(x))
		x = F.relu(self.fc3(x))
		x = F.relu(self.fc4(x))
		x = self.fc5(x)

		return x

class MyRNN2(nn.Module):
	def __init__(self):
		super(MyRNN2, self).__init__()
		self.rnn = nn.GRU(input_size=1, hidden_size=16, num_layers=1, batch_first=True, dropout=0)
		self.fc = nn.Linear(in_features=16, out_features=5)

	def forward(self, x):
		x, _ = self.rnn(x)
		x = F.relu(x)
		x = self.fc(x[:, -1, :])
		return x

class MyRNN(nn.Module):
	def __init__(self):
		super(MyRNN, self).__init__()
		self.rnn = nn.GRU(input_size=1, hidden_size=256, num_layers=2, batch_first=True, dropout=0.5)
		self.fc1 = nn.Linear(256, 128)
		self.fc2 = nn.Linear(128, 64)
		self.fc3 = nn.Linear(64, 5) 

	def forward(self, x):
		x, _ = self.rnn(x)
		x = F.relu(x)
		x = F.relu(self.fc1(x[:, -1, :]))
		x = F.relu(self.fc2(x))
		x = self.fc3(x)
		return x


class MyVariableRNN2(nn.Module):
	def __init__(self, dim_input):
		super(MyVariableRNN2, self).__init__()
		# You may use the input argument 'dim_input', which is basically the number of features
		self.fc1 = nn.Linear(in_features=int(dim_input), out_features=64)
		self.tanh = nn.Tanh()
		self.rnn = nn.GRU(input_size=64, hidden_size=16, num_layers=1, batch_first=True)
		self.fc2 = nn.Linear(in_features=16, out_features=2)


	def forward(self, input_tuple):
		# HINT: Following two methods might be useful
		# 'pack_padded_sequence' and 'pad_packed_sequence' from torch.nn.utils.rnn

		seqs, lengths = input_tuple
		seqs = self.tanh(self.fc1(seqs))
		packed_input = pack_padded_sequence(seqs, lengths.cpu(), batch_first=True)
		rnn_output, _ = self.rnn(packed_input)
		padded_output, _ = pad_packed_sequence(rnn_output, batch_first=True)
		#print(padded_output)
		#print(padded_output[:,-1,:])
		padded_output = F.relu(padded_output)
		out = self.fc2(padded_output[:, -1, :])
		return out
		

class MyVariableRNN(nn.Module):
	def __init__(self, dim_input):
		super(MyVariableRNN, self).__init__()
		# You may use the input argument 'dim_input', which is basically the number of features
		self.fc1 = nn.Linear(in_features=int(dim_input), out_features=128)
		self.fc2 = nn.Linear(128, 64)
		self.tanh = nn.Tanh()
		self.rnn = nn.GRU(input_size=64, hidden_size=16, num_layers=2, batch_first=True, dropout=0.5)
		self.fc3 = nn.Linear(in_features=16, out_features=2)




	def forward(self, input_tuple):
		# HINT: Following two methods might be useful
		# 'pack_padded_sequence' and 'pad_packed_sequence' from torch.nn.utils.rnn

		seqs, lengths = input_tuple
		seqs = F.relu(self.fc1(seqs))
		seqs = F.relu(self.fc2(seqs))
		seqs = self.tanh(seqs)
		packed_input = pack_padded_sequence(seqs, lengths.cpu(), batch_first=True)
		rnn_output, _ = self.rnn(packed_input)
		padded_output, _ = pad_packed_sequence(rnn_output, batch_first=True)
		padded_output = F.relu(padded_output)
		out = self.fc3(padded_output[:, -1, :])
		return out