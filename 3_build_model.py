#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Article Text Analyze And Tensorflow Model Build Module
# Author: t3ls (https://github/t3ls/)
# Designed for BUPT course: Practice of Large Program Design
# Create date: 2019/07/01

import tqdm
import jieba
import pymysql
import codecs
import asyncio
import ast
import os
import keras
from config import *
from numba import njit
from builtins import str
from kashgari.tasks.classification import CNNModel,CNNLSTMModel,BLSTMModel,ClassificationModel
from kashgari.embeddings import BERTEmbedding, WordEmbeddings
from keras.preprocessing.text import Tokenizer
from keras.models import Model
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, Flatten, Dropout
from keras.layers import Conv1D, MaxPooling1D, Embedding
from keras.models import Sequential
from keras.utils import to_categorical
import numpy as np
from collections import Counter
from keras.utils import plot_model
from keras.layers import Embedding
import gensim

# 初始化变量
tf_board_callback = keras.callbacks.TensorBoard(log_dir='./logs', update_freq=1000)
test_x, test_y = [], []
train_x, train_y = [], []
val_x, val_y = [], []


def test_dataset(model_dir: str) -> list:
	# 从数据库中获取正文并使用模型进行预测分类，
	# 预测结果写回数据库
	conn = pymysql.connect(host=DB_HOST,
                        port=int(DB_PORT),
                        user=DB_USER,
                        password=DB_PASS,
                        db=DB_NAME,
                        charset=DB_CHARSET
                        )
	cursor = conn.cursor()
	cursor.execute("""
		SELECT `page_text`,`page_title`,`category`,`hash` FROM `webpage_text`
		WHERE `%s_predict` IS NULL ORDER BY `time` desc
		""" % model_dir.split('.model')[0].split('/')[-1] 
		)
	all_text = []
	data = cursor.fetchall()
	# 判断预测使用的模型
	if 'cnn.model' in model_dir:
		model = CNNModel.load_model(model_dir)
	elif 'cnnlstm.model' in model_dir:
		model = CNNLSTMModel.load_model(model_dir)
	elif 'blstm.model' in model_dir:
		model = BLSTMModel.load_model(model_dir)
	for i in tqdm.tqdm(data):
		label = i[2]
		# 将文章分词，拼接标题与正文
		content = strip_stopwords(list(jieba.cut(i[0] + '。' + i[1])))
		all_text += content
		predict = model.predict(content)
		cursor.execute(
			'UPDATE `webpage_text` SET {model}_predict="{predict}"'.format(model=model_dir.split('.model')[0].split('/')[-1],predict=predict)+
			'WHERE hash="%s"' % i[3]
			)
		conn.commit()
		# print('[+] Predict:'+predict+', Label:'+label+', Title:'+i[1])

	# 计算词频并将排行前100的热词写入数据库
	c = Counter(all_text)
	i = 1
	cursor.execute(
		'DELETE FROM `hot_key` WHERE 1=1'
		)
	conn.commit()
	for k,v in c.most_common(100):
		if len(k) == 1:
			continue
		cursor.execute(
			'INSERT INTO `hot_key` VALUES ({0}, "{1}", {2})'.format(i, k, v)
			)
		conn.commit()
		i += 1
	print('[+] Success')


class h5CNNModel(ClassificationModel):
	# cnn模型
    __architect_name__ = 'h5CNNModel'
    
    def _prepare_model(self):
        base_model = self.embedding.model
        drop_out_layer = Dropout(0.3)(base_model.output)
        conv1d_layer = Conv1D(128, 3, padding='valid', activation='relu', strides=1)(drop_out_layer)
        max_pool_layer = MaxPooling1D(3)(conv1d_layer)
        flatten_layer = Flatten()(max_pool_layer)
        dense_layer_1 = Dense(200, activation='relu')(flatten_layer)
        dense_layer_2 = Dense(len(self.label2idx), activation='softmax')(dense_layer_1)
        output_layers = [dense_layer_2]
        
        self.model = Model(base_model.inputs, output_layers)

    def _compile_model(self):
        self.model.compile(optimizer='adam',
                           loss='categorical_crossentropy',
                           metrics=['accuracy'])


@njit(nogil=True)
def _rm_stopword(stopwords: list, result: list):
	# 过滤停用词的实现，使用jit进行性能优化
	for i in stopwords:
		for j in result:
			if i == j:
				result.remove(j)
	return result


def strip_stopwords(wordlist: list, stopwords_dir: str = 'cnn/stopwords') -> list:
	# 预处理数据，过滤停用词并去重
	result = wordlist[:]
	for stopwords in os.listdir(stopwords_dir):
		stopwords = stopwords_dir + '/' + stopwords
		with codecs.open(stopwords, 'r', 'utf-8') as f:
			stopwords = f.read().split('\n')
		result = _rm_stopword(stopwords, result)
	return list(set(result))


def read_file(path :str) -> (list, list):
	# 从文件中读取数据集并预处理
    lines = open(path, 'r', encoding='utf-8').read().splitlines()
    x_list = []
    y_list = []
    for line in tqdm.tqdm(lines):
        rows = line.split('\t')
        if len(rows) >= 2:
            y_list.append(rows[0])
            x_list.append(strip_stopwords(list(jieba.cut('\t'.join(rows[1:])))))
        else:
            print(rows)
    # print(x_list[0])
    return x_list, y_list


def prepare_data() -> None:
	# 加载cnews数据集，构建cache
	global test_x, test_y, train_x, train_y, val_x, val_y
	if os.path.exists('cnn/cnews/cnews.test_x.txt'):
		with codecs.open('cnn/cnews/cnews.test_x.txt', 'r', 'utf-8') as f:
			test_x = ast.literal_eval(f.read())
		with codecs.open('cnn/cnews/cnews.test_y.txt', 'r', 'utf-8') as f:
			test_y = ast.literal_eval(f.read())
	else:
		test_x, test_y = read_file('cnn/cnews/cnews.test.txt')
		with codecs.open('cnn/cnews/cnews.test_x.txt', 'w', 'utf-8') as f:
			f.write(str(test_x))
		with codecs.open('cnn/cnews/cnews.test_y.txt', 'w', 'utf-8') as f:
			f.write(str(test_y))

	if os.path.exists('cnn/cnews/cnews.train_x.txt'):
		with codecs.open('cnn/cnews/cnews.train_x.txt', 'r', 'utf-8') as f:
			train_x = ast.literal_eval(f.read())
		with codecs.open('cnn/cnews/cnews.train_y.txt', 'r', 'utf-8') as f:
			train_y = ast.literal_eval(f.read())
	else:
		train_x, train_y = read_file('cnn/cnews/cnews.train.txt')
		with codecs.open('cnn/cnews/cnews.train_x.txt', 'w', 'utf-8') as f:
			f.write(str(train_x))
		with codecs.open('cnn/cnews/cnews.train_y.txt', 'w', 'utf-8') as f:
			f.write(str(train_y))

	if os.path.exists('cnn/cnews/cnews.val_x.txt'):
		with codecs.open('cnn/cnews/cnews.val_x.txt', 'r', 'utf-8') as f:
			val_x = ast.literal_eval(f.read())
		with codecs.open('cnn/cnews/cnews.val_y.txt', 'r', 'utf-8') as f:
			val_y = ast.literal_eval(f.read())
	else:
		val_x, val_y = read_file('cnn/cnews/cnews.val.txt')
		with codecs.open('cnn/cnews/cnews.val_x.txt', 'w', 'utf-8') as f:
			f.write(str(val_x))
		with codecs.open('cnn/cnews/cnews.val_y.txt', 'w', 'utf-8') as f:
			f.write(str(val_y))



if __name__ == '__main__':
	# bert_embedding = BERTEmbedding('bert-base-chinese', sequence_length=512)
	# word2vec_embedding = WordEmbeddings('sgns.weibo.bigram', sequence_length=30)
	# prepare_data()

	# 各种模型的训练
	# cnn_model = CNNModel.load_model('cnn/cnn.model')
	# plot_model(cnn_model, to_file='cnn_model.png',show_shapes=True)
	# cnn_model = CNNModel()
	# cnn_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# cnn_model.evaluate(test_x, test_y)
	# cnn_model.save('cnn/cnn.model')

	# cnnlstm_model = CNNLSTMModel()
	# cnnlstm_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# cnnlstm_model.evaluate(test_x, test_y)
	# cnnlstm_model.save('cnn/cnnlstm.model')

	# blstm_model = BLSTMModel()
	# blstm_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# blstm_model.evaluate(test_x, test_y)
	# blstm_model.save('cnn/blstm.model')

	# cnn_embedding_model = CNNModel(embedding)
	# cnn_embedding_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# cnn_embedding_model.evaluate(test_x, test_y)
	# cnn_embedding_model.save('cnn/cnn_embedding.model')

	# cnnlstm_embedding_model = CNNLSTMModel(embedding)
	# cnnlstm_embedding_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# cnnlstm_embedding_model.evaluate(test_x, test_y)
	# cnnlstm_embedding_model.save('cnn/cnnlstm_embedding.model')

	# blstm_embedding_model = BLSTMModel(embedding)
	# blstm_embedding_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# blstm_embedding_model.evaluate(test_x, test_y)
	# blstm_embedding_model.save('cnn/blstm_embedding.model')

	# cnn_model = MyCNNModel()
	# cnn_model.fit(train_x, train_y, val_x, val_y, batch_size=128, fit_kwargs={'callbacks': [tf_board_callback]})
	# cnn_model.evaluate(test_x, test_y)
	# cnn_model.save('cnn/h5cnn.model')

	test_dataset('cnn/cnn.model')
	# test_dataset('cnn/cnnlstm.model')
	# test_dataset('cnn/blstm.model')
	# test_dataset('cnn/cnn_embedding.model')
	# test_dataset('cnn/cnnlstm_embedding.model')
	# test_dataset('cnn/blstm_embedding.model')
