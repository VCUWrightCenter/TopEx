# AUTOGENERATED! DO NOT EDIT! File to edit: preprocessing.ipynb (unless otherwise specified).

__all__ = ['decontracted', 'token_filter', 'tokenize_and_stem']

# Cell
import nltk
from nltk.tokenize import WhitespaceTokenizer
from nltk.corpus import stopwords
import numpy as np
import string
import re

# Cell
def decontracted(text:str):
    "Removes contractions from input `text`. Credit: https://stackoverflow.com/questions/19790188/expanding-english-language-contractions-in-python"
    contractions = [
        (r"won\'t", "will not"),
        (r"can\'t", "can not"),
        (r"hadn\'t", "had not"),
        (r"doesnt", "does not"),
        (r"youre", "you are"),
        (r"dont", "do not"),
        (r"im\s", "i am"),
        (r"ive\s", "i have"),
        (r"won\'t", "will not"),
        (r"can\'t", "can not"),
        (r"hadn\'t", "had not"),
        (r"dont\s", "do not"),
        (r"n\'t", " not"),
        (r"\'re", " are"),
        (r"\'s", " is"),
        (r"\'d", " would"),
        (r"\'ll", " will"),
        (r"\'t", " not"),
        (r"\'ve", " have"),
        (r"\'m", " am")
    ]

    # Replace any contractions with their decontracted equivalent
    for contraction, decontracted in contractions:
        text = re.sub(contraction, decontracted, text)

    text = re.sub(r"/", " ", text) ### I added this line (Amy)
    return text

# Cell
def token_filter(token:str, stop_words:list):
    "Returns False for stop words and tokens with no alpha characters, otherwise, True"
    match = re.match('[A-z]', token)
    return match is not None and token not in stop_words

# Cell
def tokenize_and_stem(text):
    "Parse out sentences, remove contractions, tokenize by white space, and remove all punctuation, and lemmatize tokens"
    lemmatizer = nltk.WordNetLemmatizer()
    custom_stop_words = {"patient","mrs","hi","ob","1am","4month","o2","ed","ecmo","m3","ha","3rd","ai","csicu","wa","first",
                         "second","third","fourth","etc","eg","thus",",",".","'","(",")","!","...","'m","'s",'"',"?", "`",
                         "say","many","things","new","much","get","really","since","way","also","one","two","three","four",
                         "five","six","week","day","month","year","would","could","should","like","im","thing","v","u","d","g"}
    stop_words = set(stopwords.words('english')) | custom_stop_words
    table  = str.maketrans(' ', ' ', string.punctuation+"“"+"”")
    sent = nltk.sent_tokenize(text)
    sent_tokens = []
    sent_pos = []
    sent_raw = []

    #For each sentence in document get back the list of tokenized words with contractions normalized and punctuation removed
    for s in sent:
        # Condense whitespace
        s = re.sub("\s+", " " ,s).strip()

        sent_raw.append(s)
        tokenized = WhitespaceTokenizer().tokenize(decontracted(s).translate(table))

        # Part of Speech tags
        pos_tags = nltk.pos_tag(tokenized)

        # Lemmatize and convert to lowercase
        lemma = [lemmatizer.lemmatize(t).lower() for t in tokenized]

        # Create a filter to remove stopwords (including some punctuation) and tokens with no alpha characters
        filter_mask = [token_filter(token, stop_words) for token in lemma]

        # Add filtered list of tokens and PoS tags
        filtered_tokens = list(np.array(lemma)[filter_mask])
        filtered_pos = list(np.array(pos_tags)[filter_mask])
        sent_tokens.append(filtered_tokens)
        sent_pos.append(filtered_pos)

    return sent_tokens, sent_pos, sent_raw