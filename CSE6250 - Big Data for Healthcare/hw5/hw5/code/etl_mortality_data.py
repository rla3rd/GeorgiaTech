import os
import pickle
import pandas as pd
import numpy as np

##### DO NOT MODIFY OR REMOVE THIS VALUE #####
checksum = '169a9820bbc999009327026c9d76bcf1'
##### DO NOT MODIFY OR REMOVE THIS VALUE #####

PATH_TRAIN = "../data/mortality/train/"
PATH_VALIDATION = "../data/mortality/validation/"
PATH_TEST = "../data/mortality/test/"
PATH_OUTPUT = "../data/mortality/processed/"


def convert_icd9(icd9_object):
	"""
	:param icd9_object: ICD-9 code (Pandas/Numpy object).
	:return: extracted main digits of ICD-9 code
	"""
	icd9_str = str(icd9_object)
	# TODO: Extract the the first 3 or 4 alphanumeric digits prior to the decimal point from a given ICD-9 code.
	# TODO: Read the homework description carefully.
	if icd9_str.lower() not in ('nan', 'inf', 'none', ''):
		if icd9_str[0] == 'E':
			icd9_str = icd9_str[:4]
		else:
			icd9_str = icd9_str[:3]
		converted = icd9_str
	else:
		converted = None

	return converted


def build_codemap(df_icd9, transform):
	"""
	:return: Dict of code map {main-digits of ICD9: unique feature ID}
	"""
	# TODO: We build a code map using ONLY train data. Think about how to construct validation/test sets using this.
	df_digits = df_icd9['ICD9_CODE'].apply(transform)
	df_digits = df_digits.copy()
	df_digits = df_digits.unique()
	df_digits = df_digits[df_digits != np.array(None)]	
	df_digits = np.sort(df_digits)
	codemap = dict(zip(df_digits, np.arange(len(df_digits))))
	return codemap


def create_dataset(path, codemap, transform):
	"""
	:param path: path to the directory contains raw files.
	:param codemap: 3-digit ICD-9 code feature map
	:param transform: e.g. convert_icd9
	:return: List(patient IDs), List(labels), Visit sequence data as a List of List of List.
	"""
	# TODO: 1. Load data from the three csv files
	# TODO: Loading the mortality file is shown as an example below. Load two other files also.
	# TODO: 2. Convert diagnosis code in to unique feature ID.
	# TODO: HINT - use 'transform(convert_icd9)' you MORTALITYimplemented and 'codemap'.
	# TODO: 3. Group the diagnosis codes for the same visit.
	# TODO: 4. Group the visits for the same patient.
	# TODO: 5. Make a visit sequence dataset as a List of patient Lists of visit Lists
	# TODO: Visits for each patient must be sorted in chronological order.
	# TODO: 6. Make patient-id List and label List also.
	# TODO: The order of patients in the three List output must be consistent.

	#patient_ids = [0, 1, 2]
	#labels = [1, 0, 1]
	#seq_data = [[[0, 1], [2]], [[1, 3, 4], [2, 5]], [[3], [5]]]

	df_mortality = pd.read_csv(os.path.join(path, "MORTALITY.csv"))
	df_adm = pd.read_csv(os.path.join(path, "ADMISSIONS.csv"))
	df_diag = pd.read_csv(os.path.join(path, "DIAGNOSES_ICD.csv"))

	codemap = build_codemap(df_diag[['ICD9_CODE']], convert_icd9)
	df_diag['ICD9_CODE'] = df_diag['ICD9_CODE'].apply(convert_icd9)
	df_adm['ADMITTIME'] = df_adm['ADMITTIME'].apply(lambda x: x.split(" ")[0])
	df_adm = df_adm.merge(df_diag[['HADM_ID', 'ICD9_CODE']], how='inner', on=['HADM_ID'])[['SUBJECT_ID', 'HADM_ID', 'ADMITTIME', 'ICD9_CODE']].copy()
	df_adm.drop_duplicates(inplace=True)
	df_adm.sort_values(['HADM_ID', 'ADMITTIME'], inplace=True) # 'SUBJECT_ID', 
	df_adm['ICD9_CODE'] = df_adm['ICD9_CODE'].apply(lambda x: codemap.get(x))
	df_adm.dropna(inplace=True)

	mortality = dict(zip(df_mortality['SUBJECT_ID'], df_mortality['MORTALITY']))
	patient_ids = sorted(list(mortality.keys()))
	labels = []
	seq_data = []
	for p in patient_ids:
		labels.append(mortality[p])
		grouped = df_adm[df_adm['SUBJECT_ID'] == p].groupby(['SUBJECT_ID', 'ADMITTIME'])['ICD9_CODE'].apply(list).reset_index(name='ICD9_CODE')
		seq_data.append(grouped['ICD9_CODE'].to_list())

	return patient_ids, labels, seq_data


def main():
	# Build a code map from the train set
	print("Build feature id map")
	df_icd9 = pd.read_csv(os.path.join(PATH_TRAIN, "DIAGNOSES_ICD.csv"), usecols=["ICD9_CODE"])
	codemap = build_codemap(df_icd9, convert_icd9)
	os.makedirs(PATH_OUTPUT, exist_ok=True)
	pickle.dump(codemap, open(os.path.join(PATH_OUTPUT, "mortality.codemap.train"), 'wb'), pickle.HIGHEST_PROTOCOL)

	# Train set
	print("Construct train set")
	train_ids, train_labels, train_seqs = create_dataset(PATH_TRAIN, codemap, convert_icd9)

	pickle.dump(train_ids, open(os.path.join(PATH_OUTPUT, "mortality.ids.train"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(train_labels, open(os.path.join(PATH_OUTPUT, "mortality.labels.train"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(train_seqs, open(os.path.join(PATH_OUTPUT, "mortality.seqs.train"), 'wb'), pickle.HIGHEST_PROTOCOL)

	# Validation set
	print("Construct validation set")
	validation_ids, validation_labels, validation_seqs = create_dataset(PATH_VALIDATION, codemap, convert_icd9)

	pickle.dump(validation_ids, open(os.path.join(PATH_OUTPUT, "mortality.ids.validation"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(validation_labels, open(os.path.join(PATH_OUTPUT, "mortality.labels.validation"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(validation_seqs, open(os.path.join(PATH_OUTPUT, "mortality.seqs.validation"), 'wb'), pickle.HIGHEST_PROTOCOL)

	# Test set
	print("Construct test set")
	test_ids, test_labels, test_seqs = create_dataset(PATH_TEST, codemap, convert_icd9)

	pickle.dump(test_ids, open(os.path.join(PATH_OUTPUT, "mortality.ids.test"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(test_labels, open(os.path.join(PATH_OUTPUT, "mortality.labels.test"), 'wb'), pickle.HIGHEST_PROTOCOL)
	pickle.dump(test_seqs, open(os.path.join(PATH_OUTPUT, "mortality.seqs.test"), 'wb'), pickle.HIGHEST_PROTOCOL)

	print("Complete!")


if __name__ == '__main__':
	main()
