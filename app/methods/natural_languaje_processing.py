import re
import string
import time
import spacy
from unidecode import unidecode

POS_tagger = spacy.load('es_dep_news_trf')

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

def get_nouns(text, top_n = 5):
    tagged_words = POS_tagger(text.lower())
    nouns_string = ""
    lemma_freq = {}
    for word in tagged_words:
        if word.pos_ == 'NOUN': 
            if word.lemma_ not in lemma_freq: lemma_freq[word.lemma_] = 0
            lemma_freq[word.lemma_] += 1
    sort_lemma_freq = sorted(lemma_freq.items(), key=lambda x: x[1], reverse=True)
    for noun in sort_lemma_freq[:top_n]: nouns_string += (' ' + noun[0])
    return nouns_string.strip()