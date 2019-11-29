# load the libraries for the Inference Class
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
sys.path.append('/home/webwerks/patricia/project/project-hiring-bot/Toxic-Comment-Filter/Django/')

import csv
import os
import logging
import argparse
import random
from tqdm import tqdm, trange
import pandas as pd

import yaml
import torch
import numpy as np
import torch.nn.functional as F
import pprint
from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from torch.utils.data.distributed import DistributedSampler

from helper.tokenization import BertTokenizer
from helper.modeling import BertForSequenceClassification
from helper.optimization import BertAdam
from helper.file_utils import PYTORCH_PRETRAINED_BERT_CACHE



# # loading the config from the global config yaml

# with open("./config/global_config.yml", "r") as filename:
# 	config = yaml.load(filename)
# output_model_file = config["inference_bert"]["output_model_file"]
# bert_model= config["inference_bert"]["bert_model"]
# max_seq_length = config["inference_bert"]["max_seq_length"]
# with open(config["inference_bert"]["labels"], 'r') as read_file:
# 	labels = list(map(lambda x: x.strip('\n'), read_file.readlines()))
# 	num_labels = len(labels)


# helper classes
class InputExample(object):
	"""A single training/test example for simple sequence classification."""

	def __init__(self, guid, text_a, text_b, label=None):
		"""Constructs a InputExample.

		Args:
			guid: Unique id for the example.
			text_a: string. The untokenized text of the first sequence. For single
			sequence tasks, only this sequence must be specified.
			text_b: (Optional) string. The untokenized text of the second sequence.
			Only must be specified for sequence pair tasks.
			label: (Optional) string. The label of the example. This should be
			specified for train and dev examples, but not for test examples.
		"""
		self.guid = guid
		self.text_a = text_a
		self.text_b = text_b
		self.label = label


class InputFeatures(object):
	"""A single set of features of data."""

	def __init__(self, input_ids, input_mask, segment_ids, label_id):
		self.input_ids = input_ids
		self.input_mask = input_mask
		self.segment_ids = segment_ids
		self.label_id = label_id


class Inference():
	def __init__(self, bert_model, num_labels, labels, output_model_file, max_seq_length):
		"""
		Args:
		num_labels : Number of target labels
		bert_model : Name of the pretrained model to be used
		task_name  : Name of the task (incase different datasets are used)
		output_dir : Directory containing the pytorch.bin file (model)
		labels     : List of target labels
		
		"""
		self.bert_model = bert_model
		self.num_labels = num_labels
		self.labels = labels
		self.max_seq_length = max_seq_length
		self.reverse_label_map = None
		self.device = torch.device("cuda" if torch.cuda.is_available()  else "cpu")
		self.model = self.load_model(output_model_file)

	
	def load_model(self, output_model_file):
		""" load the model from the .bin file """
		model_state_dict = torch.load(output_model_file)
		model = BertForSequenceClassification.from_pretrained(self.bert_model, state_dict= model_state_dict, num_labels = self.num_labels)
		model.to(self.device)
		return model

	def _truncate_seq_pair(self, tokens_a, tokens_b, max_length):
		"""Truncates a sequence pair in place to the maximum length."""

		# This is a simple heuristic which will always truncate the longer sequence
		# one token at a time. This makes more sense than truncating an equal percent
		# of tokens from each, since if one sequence is very short then each token
		# that's truncated likely contains more information than a longer sequence.
		while True:
			total_length = len(tokens_a) + len(tokens_b)
			if total_length <= max_length:
				break
			if len(tokens_a) > len(tokens_b):
				tokens_a.pop()
			else:
				tokens_b.pop()
				
	def get_features(self, para, label_list, tokenizer, max_seq_length):
		""" Convert the given sentence into the model input format """
		label_map = {label : i for i, label in enumerate(label_list)}
#         self.reverse_label_map = {v: k for k, v in label_map.items()}
		guid = "%s-%s" % ("test", 1)
		text_a = para["model_answer"]
		text_b = para["candidate_answer"]
		label = label_list[0]
		example = InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label)
		
		tokens_a = tokenizer.tokenize(example.text_a)

		tokens_b = tokenizer.tokenize(example.text_b)
		if example.text_b:
			tokens_b = tokenizer.tokenize(example.text_b)
			# Modifies `tokens_a` and `tokens_b` in place so that the total
			# length is less than the specified length.
			# Account for [CLS], [SEP], [SEP] with "- 3"
			self._truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
		else:
			# Account for [CLS] and [SEP] with "- 2"
			if len(tokens_a) > max_seq_length - 2:
				tokens_a = tokens_a[:(max_seq_length - 2)]

		# The convention in BERT is:
		# (a) For sequence pairs:
		#  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
		#  type_ids: 0   0  0    0    0     0       0 0    1  1  1  1   1 1
		# (b) For single sequences:
		#  tokens:   [CLS] the dog is hairy . [SEP]
		#  type_ids: 0   0   0   0  0     0 0
		#
		# Where "type_ids" are used to indicate whether this is the first
		# sequence or the second sequence. The embedding vectors for `type=0` and
		# `type=1` were learned during pre-training and are added to the wordpiece
		# embedding vector (and position vector). This is not *strictly* necessary
		# since the [SEP] token unambigiously separates the sequences, but it makes
		# it easier for the model to learn the concept of sequences.
		#
		# For classification tasks, the first vector (corresponding to [CLS]) is
		# used as as the "sentence vector". Note that this only makes sense because
		# the entire model is fine-tuned.
		tokens = ["[CLS]"] + tokens_a + ["[SEP]"]
		segment_ids = [0] * len(tokens)

		if tokens_b:
			tokens += tokens_b + ["[SEP]"]
			segment_ids += [1] * (len(tokens_b) + 1)

		input_ids = tokenizer.convert_tokens_to_ids(tokens)

		# The mask has 1 for real tokens and 0 for padding tokens. Only real
		# tokens are attended to.
		input_mask = [1] * len(input_ids)

		# Zero-pad up to the sequence length.
		padding = [0] * (max_seq_length - len(input_ids))
		input_ids += padding
		input_mask += padding
		segment_ids += padding

		assert len(input_ids) == max_seq_length
		assert len(input_mask) == max_seq_length
		assert len(segment_ids) == max_seq_length
		label_id = label_map[example.label]
#         print("*** Example ***")
#         print("guid: %s" % (example.guid))
#         print("tokens: %s" % " ".join(
#                 [str(x) for x in tokens]))
#         print("input_ids: %s" % " ".join([str(x) for x in input_ids]))
#         print("input_mask: %s" % " ".join([str(x) for x in input_mask]))
#         print("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))

		
		return InputFeatures(input_ids=input_ids,
							  input_mask=input_mask,
							  segment_ids=segment_ids,
							  label_id=label_id)

		
	
	def predict(self, eval_features):
		""" Returns the final prediction of the given sentence with a probability score"""
		input_ids = torch.tensor(eval_features.input_ids, dtype=torch.long).to(self.device).unsqueeze(0)
		input_mask = torch.tensor(eval_features.input_mask, dtype=torch.long).to(self.device).unsqueeze(0)
		segment_ids = torch.tensor(eval_features.segment_ids, dtype=torch.long).to(self.device).unsqueeze(0)
		
		with torch.no_grad():
			logits = self.model(input_ids, segment_ids, input_mask)
			logits = logits.to("cpu")
			softmax_logits = F.softmax(logits[0], dim=0).numpy()
			print("softmax score : ", softmax_logits)
#             final_logits = list(zip(list(map(lambda x : self.reverse_label_map[np.ravel(np.where(softmax_logits==x))[0]], softmax_logits )), softmax_logits))
		pred = np.argmax(softmax_logits)
		prob = np.max(softmax_logits)
		
		return pred , prob
	
	
	def main(self, data):
		""" Calls the required function"""
		tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", do_lower_case=True)
		eval_features = self.get_features(data, self.labels, tokenizer, self.max_seq_length)
		label, prob = self.predict(eval_features)
		return label, prob


# # loading the class object
# prediction_obj = Inference(bert_model = bert_model, num_labels = num_labels, labels = labels, 
# 							 output_model_file = output_model_file, max_seq_length = max_seq_length )





# ## test run
# excel_path = '/home/webwerks/patricia/project/project-hiring-bot/Toxic-Comment-Filter/test-data/python-data/full-data-python-20-questions.xlsx'
# result_df = []
# total_correct_count , total_count = 0, 20
# df_correct = pd.read_excel(open(excel_path, 'rb'), sheetname='correct-dataset')
# df_candidate = pd.read_excel(open(excel_path, 'rb') , sheetname='candidate-dataset')
# answer_rows = df_correct.columns.to_list()
# answer_rows.remove('Questions') 
# answer_rows.remove('Index') 
# for c_index, candidate_row in df_candidate.iterrows():
# 	candidate_ans = ''
# 	question_index = candidate_row['Index']
# 	candidate_ans = candidate_row['Candidate_Ans']
# 	for correct_index, correct_row in df_correct.iterrows():
# 		correct_ans_index = correct_row['Index']
# 		if question_index == correct_ans_index:
# 			for each_ans in answer_rows:
# 				model_ans = ''
# 				model_ans = correct_row[each_ans]
# 				inter_result = {"candidate_answer" : candidate_ans, "model_answer" : model_ans}
# 				inter_result['pred'] , inter_result['probabilty'] = prediction_obj.main(inter_result)
# 				result_df.append(inter_result)
# result_df = pd.DataFrame(result_df)
# # writing into a dataframe
# result_df.to_excel("./output-priyanka.xlsx", sheet_name='report-card')