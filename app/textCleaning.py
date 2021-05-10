import re
import string
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

def stemmer(text):
    with open('app/spanish_stopwords.txt', 'r') as f:
        stopwords = [unidecode(word.strip()) for word in f]
    text_words = [unidecode(word.strip()) for word in text.split(' ')]
    text_words = [word for word in text_words if word not in stopwords]
    return ' '.join(text_words)