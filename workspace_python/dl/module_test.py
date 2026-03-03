import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

import warnings
warnings.filterwarnings(action='ignore')

#----- 텐서플로우 & 넘피 시드 고정
import tensorflow as tf
tf.random.set_seed(7589)
np.random.seed(7589)

#----- 딥러닝 모델 - FC
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical
#----- 딥러닝 모델 - CNN
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense


#----- 딥러닝 모델 - FC, CNN
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.utils import to_categorical

#----- 조기종료, 모델저장
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping

from gensim.models import KeyedVectors



import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import WordPunctTokenizer
from tensorflow.keras.preprocessing.text import text_to_word_sequence


from tensorflow.keras.preprocessing.text import Tokenizer

from konlpy.tag import Okt
import MeCab


print("정상")