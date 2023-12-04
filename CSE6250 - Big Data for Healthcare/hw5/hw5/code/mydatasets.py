import numpy as np
import pandas as pd
from scipy import sparse
import torch
from torch.utils.data import TensorDataset, Dataset

##### DO NOT MODIFY OR REMOVE THIS VALUE #####
checksum = '169a9820bbc999009327026c9d76bcf1'
##### DO NOT MODIFY OR REMOVE THIS VALUE #####

def load_seizure_dataset(path, model_type):
	"""
	:param path: a path to the seizure data CSV file
	:return dataset: a TensorDataset consists of a data Tensor and a target Tensor
	"""
	# TODO: Read a csv file from path.
	# TODO: Please refer to the header of the file to locate X and y.
	# TODO: y in the raw data is ranging from 1 to 5. Change it to be from 0 to 4.
	# TODO: Remove the header of CSV file of course.
	# TODO: Do Not change the order of rows.
	# TODO: You can use Pandas if you want to.
	df = pd.read_csv(path)
	X = df.iloc[:, :-1].values
	Y = df.iloc[:, -1].values
	Y = Y - 1

	if model_type == 'MLP':
		data = torch.from_numpy(X.astype('float32'))
		target = torch.from_numpy(Y.astype('long'))
		dataset = TensorDataset(data, target)
	elif model_type == 'CNN':
		data = torch.from_numpy(X.astype('float32')).unsqueeze(1)
		target = torch.from_numpy(Y.astype('long'))
		dataset = TensorDataset(data, target)
	elif model_type == 'RNN':
		data = torch.from_numpy(X[:, :, None].astype('float32'))
		target = torch.from_numpy(Y.astype('long'))
		dataset = TensorDataset(data, target)
	else:
		raise AssertionError("Wrong Model Type!")

	return dataset


def calculate_num_features(seqs):
	"""
	:param seqs:
	:return: the calculated number of features
	"""
	max_d = 0
	for patient in seqs:
		for visit in patient:
			for d in visit:
				if d >= max_d:
					max_d = d
	return int(max_d + 1)

class VisitSequenceWithLabelDataset(Dataset):
	def __init__(self, seqs, labels, num_features):
		"""
		Args:
			seqs (list): list of patients (list) of visits (list) of codes (int) that contains visit sequences
			labels (list): list of labels (int)
			num_features (int): number of total features available
		"""

		if len(seqs) != len(labels):
			raise ValueError("Seqs and Labels have different lengths")

		self.labels = labels

		# TODO: Complete this constructor to make self.seqs as a List of which each element represent visits of a patient
		# TODO: by Numpy matrix where i-th row represents i-th visit and j-th column represent the feature ID j.
		# TODO: You can use Sparse matrix type for memory efficiency if you want.
		self.seqs = []
		for patient in seqs:
			m = np.zeros((int(len(patient)), int(num_features)))
			j = 0
			for visit in patient:
				for d in visit:
					m[j, int(d)] = 1
			# m = sparse.csr_matrix(m)
			self.seqs.append(m)

	def __len__(self):
		return len(self.labels)

	def __getitem__(self, index):
		# returns will be wrapped as List of Tensor(s) by DataLoader
		return self.seqs[index], self.labels[index]


def visit_collate_fn(batch):
	"""
	DataLoaderIter call - self.collate_fn([self.dataset[i] for i in indices])
	Thus, 'batch' is a list [(seq_1, label_1), (seq_2, label_2), ... , (seq_N, label_N)]
	where N is minibatch size, seq_i is a Numpy (or Scipy Sparse) array, and label is an int value

	:returns
		seqs (FloatTensor) - 3D of batch_size X max_length X num_features
		lengths (LongTensor) - 1D of batch_size
		labels (LongTensor) - 1D of batch_size
	"""

	# TODO: Return the following two things
	# TODO: 1. a tuple of (Tensor contains the sequence data , Tensor contains the length of each sequence),
	# TODO: 2. Tensor contains the label of each sequence 
	tmp_lengths = []
	tmp_seqs = []
	tmp_labels = []
	num_features = None
	for row in batch:
		s = row[0]
		l = row[1]
		if s.ndim == 1:
			n = s.shape[0]
			m = 1
			
		else:
			m, n = s.shape
		tmp_seqs.append(s)
		tmp_lengths.append(m)
		tmp_labels.append(l)
		if num_features is None:
			num_features = n

	lidx = []
	for i in range(len(tmp_lengths)):
		lidx.append([tmp_lengths[i], i])
	
	lidx = sorted(lidx, key=lambda x: x[0], reverse=True)
	length = lidx[0][0]
	lengths = []
	seqs = []
	labels = []
	for row in lidx:
		i = row[1]
		lengths.append(tmp_lengths[i])
		labels.append(tmp_labels[i])
		s = tmp_seqs[i].reshape(-1)
		if s.ndim == 1:
			s = s[None,:]
		diff = length * num_features - len(s.reshape(-1))
		s = np.append(s, np.zeros(diff))
		s = s.reshape(length, num_features)
		seqs.append(s)
	
	seqs_tensor = torch.FloatTensor(seqs)
	lengths_tensor = torch.LongTensor(lengths)
	labels_tensor = torch.LongTensor(labels)

	return (seqs_tensor, lengths_tensor), labels_tensor
