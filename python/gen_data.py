import numpy as np
import os
import sys
import random
import pickle
import argparse
import pprint

from utils.data_generation_library import lemmatize

from utils.data_generation_library import imagenet_encoder
from utils.data_generation_library import imagenet_glove_encoder, imagenet_bert_pretrained_encoder

from utils.data_generation_library import openimage_encoder
from utils.data_generation_library import openimage_glove_encoder

from utils.data_generation_library import vg_noun_encoder, vg_verb_encoder
from utils.data_generation_library import vg_glove_encoder, vg_bert_pretrained_encoder, vg_gptj_pretrained_encoder

from utils.data_generation_library import vrd_noun_encoder, vrd_verb_encoder
from utils.data_generation_library import vrd_glove_encoder, vrd_bert_pretrained_encoder

from utils.data_generation_library import mit_resnet3d50_encoder, mit_swav_encoder
from utils.data_generation_library import mit_glove_encoder, mit_bert_pretrained_encoder, mit_gptj_pretrained_encoder

def load_concept(concept_file):
	words = list()
	with open("../data/concepts/"+concept_file, 'r', encoding="utf-8") as f:
		for line in f:
			word = str(line).replace('\n','').replace('\r','')
			words.append(word)
	return words

def get_encoders(dataset,l_encoder,v_encoder):
	# choose visual encoder and language encoder according to the setting
	if "imagenet" in dataset:
		if l_encoder=="glove" and v_encoder=="swav":
			visual_encoder = imagenet_encoder
			language_encoder = imagenet_glove_encoder
		elif l_encoder=="bert" and v_encoder=="swav":
			visual_encoder = imagenet_encoder
			language_encoder = imagenet_bert_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "openimage" in dataset:
		if l_encoder=="glove" and v_encoder=="swav":
			visual_encoder = openimage_encoder
			language_encoder = openimage_glove_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "vg_noun" in dataset:
		if l_encoder == "glove" and v_encoder == "swav":
			visual_encoder = vg_noun_encoder
			language_encoder = vg_glove_encoder
		elif l_encoder == "bert" and v_encoder == "swav":
			visual_encoder = vg_noun_encoder
			language_encoder = vg_bert_pretrained_encoder
		elif l_encoder == "gptj" and v_encoder == "swav":
			visual_encoder = vg_noun_encoder
			language_encoder = vg_gptj_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "vg_verb" in dataset:
		if l_encoder == "glove" and v_encoder == "swav":
			visual_encoder = vg_verb_encoder
			language_encoder = vg_glove_encoder
		elif l_encoder == "bert" and v_encoder == "swav":
			visual_encoder = vg_verb_encoder
			language_encoder = vg_bert_pretrained_encoder
		elif l_encoder == "gptj" and v_encoder == "swav":
			visual_encoder = vg_verb_encoder
			language_encoder = vg_gptj_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "vrd_noun" in dataset:
		if l_encoder == "glove" and v_encoder == "swav":
			visual_encoder = vrd_noun_encoder
			language_encoder = vrd_glove_encoder
		elif l_encoder == "bert" and v_encoder == "swav":
			visual_encoder = vrd_noun_encoder
			language_encoder = vrd_bert_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "vrd_verb" in dataset:
		if l_encoder == "glove" and v_encoder == "swav":
			visual_encoder = vrd_verb_encoder
			language_encoder = vrd_glove_encoder
		elif l_encoder == "bert" and v_encoder == "swav":
			visual_encoder = vrd_verb_encoder
			language_encoder = vrd_bert_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	elif "mit" in dataset:
		if l_encoder=="glove" and v_encoder=="swav":
			visual_encoder = mit_swav_encoder
			language_encoder = mit_glove_encoder
		elif l_encoder=="bert" and v_encoder=="swav":
			visual_encoder = mit_swav_encoder
			language_encoder = mit_bert_pretrained_encoder
		elif l_encoder == "gptj" and v_encoder == "swav":
			visual_encoder = mit_swav_encoder
			language_encoder = mit_gptj_pretrained_encoder
		else:
			print('Error, cannot find corresponding encoder(s).')
			sys.exit(1)
	else:
		print('Error, wrong dataset name.')
		sys.exit(1)
	return visual_encoder,language_encoder

def generate_embeddings(dataset,l_encoder,v_encoder,concept_file,n_sample,embeds_path=None,load_l=False,load_v=False,dump=True,cuda=False):

	name = "_".join([dataset, v_encoder, l_encoder, str(n_sample)])

	# load concepts
	concepts=load_concept(concept_file)

	visual_encoder,language_encoder=get_encoders(dataset,l_encoder,v_encoder)

	if 'openimage' in dataset:
		# lowercase the first letter in each concept word
		normalized_concepts = [concept.lower() for concept in concepts]
	elif 'vg' in dataset:
		# drop wordnet annotation suffixes in concepts
		normalized_concepts=[concept.split(".")[0] for concept in concepts]
	elif 'mit' in dataset:
		# transform concepts from present participle to simple present
		normalized_concepts=list(lemmatize(concepts).keys())
	else:
		normalized_concepts=concepts

	if embeds_path:
		loaded_struct=pickle.load(open(embeds_path,"rb"))

	if load_v and embeds_path:
		print(f"---Read visual embeddings from data/dumped_embeddings/{embeds_path}---")
		visual_embeddings=dict()
		for concept in normalized_concepts:
			visual_embeddings[concept]=loaded_struct["embeds"][concept]["visual"]
	else:
		print("---Start sampling visual embeddings---")
		visual_embeddings=visual_encoder(concepts,n_sample,name,cuda)

	if load_l and embeds_path:
		print(f"---Read language embeddings from data/dumped_embeddings/{embeds_path}---")
		language_embeddings=dict()
		for concept in normalized_concepts:
			language_embeddings[concept]=loaded_struct["embeds"][concept]["language"]
		language_embeddings=np.array(language_embeddings)
	else:
		print("---Start sampling language embeddings---")
		language_embeddings=language_encoder(concepts,n_sample,cuda)

	embed_dict = dict()
	for concept in normalized_concepts:
		embed_dict[concept]=dict(visual=visual_embeddings[concept],language=language_embeddings[concept])

	return_struct=dict(embeds=embed_dict,words=normalized_concepts)
	if dump:
		pickle.dump(return_struct,
					open(f'../data/dumped_embeddings_for_pub/{name}.pkl', 'wb'))
		print(f"Embeddings dumped to data/dumped_embeddings_for_pub/{name}.pkl")
	return return_struct

if __name__ == '__main__':

	print("gen_data.py")

	parser = argparse.ArgumentParser()
	parser.add_argument("dataset", help="name of the dataset in one of the following choices: vg_noun, vg_verb, mit")
	parser.add_argument("concept_file", help="name of the concept file")
	parser.add_argument("l_encoder", help="name of the language encoder in one of the following choices: glove, bert")
	parser.add_argument("v_encoder", help="name of the visual encoder in one of the following choices: swav, resnet3d50 (mit dataset only)")
	#parser.add_argument("--extra_info", help="extra information to identify data generation settings")
	parser.add_argument("--n_sample", type=int, default=1, help="number of sample to generate per concept")
	parser.add_argument("--embeds_path", help="path to a previously dumped struct (if needed)")
	parser.add_argument("--load_l", action="store_true", help="whether to load language embeddings from a previously dumped struct")
	parser.add_argument("--load_v", action="store_true", help="whether to load visual embeddings from a previously dumped struct")
	parser.add_argument("--dump", action="store_false", help="dump generated embeddings (by default True)")
	parser.add_argument("--cuda", action="store_true", help="use cuda (by default False)")
	args = parser.parse_args()

	print("Echo arguments:",args)
	generate_embeddings(dataset=args.dataset,
						l_encoder=args.l_encoder,
						v_encoder=args.v_encoder,
						concept_file=args.concept_file,
						n_sample=args.n_sample,
						embeds_path=args.embeds_path,
						load_l=args.load_l,
						load_v=args.load_v,
						dump=args.dump,
						cuda=args.cuda)
