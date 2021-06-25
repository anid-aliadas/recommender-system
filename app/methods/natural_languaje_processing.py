import re
import string
import nltk
from unidecode import unidecode


def clean_text_round1(text):
    '''Make text lowercase, remove text in square brackets, remove punctuation and remove words containing numbers.'''
    text = text.lower()
    text = re.sub('\[.*?¿\]\%', ' ', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), ' ', text)
    text = re.sub('\s+',' ', text)
    text = re.sub('\w*\d\w*', '', text)
    return text

def clean_text_round2(text):
    '''Get rid of some additional punctuation and non-sensical text that was missed the first time around.'''
    text = re.sub('[‘’“”…«»]', '', text)
    text = re.sub('\n', ' ', text)
    return text

def accent_mark_removal(text):
    with open('app/files/natural_languaje_processing/spanish_stopwords.txt', 'r') as f:
        stopwords = [unidecode(word.strip()) for word in f]
    text_words = [unidecode(word.strip()) for word in text.split(' ')]
    text_words = [word for word in text_words if word not in stopwords]
    return ' '.join(text_words)

def get_top_vocabulary(X, vec, top_n):
    sum_corpus_words = X.sum(axis=0)
    words_freq = [(word, sum_corpus_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
    return [word for word, freq in words_freq[:top_n]]

def get_nouns(text):
    tokenized_text = text.split()
    nouns_string = nltk.pos_tag(tokenized_text)
    return nouns_string