# AUTOGENERATED! DO NOT EDIT! File to edit: Core.ipynb (unless otherwise specified).

__all__ = ['import_docs', 'sentences_to_disk', 'get_doc_top_phrases', 'get_doc_word_vectors_tfidf',
           'get_doc_word_vectors_svd', 'get_doc_word_vectors_umap', 'get_doc_word_vectors_pretrained',
           'get_doc_word_vectors_local', 'filter_sentences', 'get_optimal_k', 'get_cluster_assignments_kmeans']

# Cell
import matplotlib.pyplot as plt
from .nlp_helpers import *
from .preprocessing import *
import numpy
from scipy.cluster.hierarchy import ward, cut_tree
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
import os
from sklearn.decomposition import TruncatedSVD
import umap.umap_ as umap

# Cell
def import_docs(path_to_file_list, verbose = False):
    "Imports and processes the list of documents contained in the given file"

    # Extract list of files from text document
    with open(path_to_file_list) as file:
        file_list = file.read().strip().split('\n')

    # Append the raw contents of each document to an array
    file_content = []
    for file_path in file_list:
        with open(file_path, "r") as file:
            text = file.read()
            file_content.append(text)

    my_docs = []
    my_docs_pos = []
    my_docs_loc = []
    raw_docs = []
    raw_sentences = []

    for doc in file_content:
        split_sent, split_sent_pos, split_sent_loc, tokens, pos, loc, full_sent, full_pos, full_loc, raw_sent = tokenize_and_stem(doc)
        my_docs.append(split_sent)
        my_docs_pos.append(split_sent_pos)
        my_docs_loc.append(split_sent_loc)
        raw_docs.append(doc)
        raw_sentences.append(raw_sent)

    if verbose == True: print("Number of Documents Loaded: " + str(len(my_docs)))

    return my_docs, my_docs_pos, my_docs_loc, raw_sentences, raw_docs

# Cell
def sentences_to_disk(raw_sentences, outfile_name):
    "Writes the raw sentences to a file organized by document and sentence number"
#     outfile_name = args.o + "/" + args.p + "_DocumentSentenceList.txt"
    with open(outfile_name, "w") as outfile:
        outfile.write("Sentence ID\tSentence Text\n")
        for doc_ix, doc in enumerate(raw_sentences):
            for sent_ix, sent in enumerate(doc):
                outfile.write(f"doc.{doc_ix}.sent.{sent_ix}\t{sent}\n")

# Cell
def get_doc_top_phrases(raw_docs, feature_names, tdm, window_size = 6, include_input_in_tfidf = False):
#     """
#     feature_names = dictionary.token2id
#     tdm = tfidf_dense
#     """
    #TODO: Do this without reparsing each sentence in get_top_phrases
    doc_top_phrases = []
    for doc_id, text in enumerate(raw_docs):
        top_phrases = get_top_phrases(doc_id, text, feature_names, tdm, window_size, include_input_in_tfidf)
        doc_top_phrases.append(top_phrases)

    return doc_top_phrases

# Cell
def get_doc_word_vectors_tfidf(doc_top_phrases, dictionary, tfidf_dense):
    "Uses the TF-IDF matrix to create a list of lists corresponding to a word vectors for the top phrases of each sentence in each document"
    return get_phrase_vec_tfidf(doc_top_phrases, dictionary, tfidf_dense)

def get_doc_word_vectors_svd(doc_top_phrases, dictionary, tfidf_dense, dimensions = 2):
    "Decomposes the TF-IDF matrix via SVD and uses the result to create a list of lists corresponding to a word vectors for the top phrases of each sentence in each document"
    svd =  TruncatedSVD(n_components = dimensions, random_state = 42)
    tfidf_transf = svd.fit_transform(tfidf_dense)
    return get_phrase_vec_tfidf(doc_top_phrases, dictionary, tfidf_transf)

def get_doc_word_vectors_umap(doc_top_phrases, dictionary, tfidf_dense, umap_neighbors = 15, dimensions = 2):
    "Transforms the TF-IDF matrix via UMAP and uses the result to create a list of lists corresponding to a word vectors for the top phrases of each sentence in each document"
    reducer = umap.UMAP(n_neighbors=umap_neighbors, min_dist=.1, metric='cosine', random_state=42, n_components = dimensions)
    embed = reducer.fit_transform(tfidf_dense)
    return get_phrase_vec_tfidf(doc_top_phrases, dictionary, embed)

def get_doc_word_vectors_pretrained(doc_top_phrases, path_to_w2v_bin_file):
    "Uses pretrained Word2Vec embeddings to create a list of lists corresponding to a word vectors for the top phrases of each sentence in each document"
    assert os.path.exists(path_to_w2v_bin_file), f'The file {path_to_w2v_bin_file} does not exist'
    model = w2v_pretrained(path_to_w2v_bin_file)
    return get_phrase_vec_w2v(doc_top_phrases, model)

def get_doc_word_vectors_local(doc_top_phrases, raw_docs, my_docs):
    "Creates Word2Vec embeddings from the input corpus and uses them to create a list of lists corresponding to a word vectors for the top phrases of each sentence in each document"
    model = w2v_from_corpus(raw_docs, my_docs)
    return get_phrase_vec_w2v(doc_top_phrases, model)

# Cell
def filter_sentences(doc_phrase_vecs, doc_top_phrases):
    "Filter the sentences, removing any that contain zero 'top phrases'"
    just_phrase_vecs = []
    just_phrase_ids = []
    just_phrase_text = []

    # Getting all phrases which have
    # Iterate documents
    for doc_ix, phrase_vecs in enumerate(doc_phrase_vecs):
        # Iterate sentences (each sentence has a phrase vector)
        for phrase_ix, phrase_vec in enumerate(phrase_vecs):
            phrase_id = f"doc.{doc_ix}.sent.{phrase_ix}"
            this_text = doc_top_phrases[doc_ix][phrase_ix]

            # Check phrase_vec is not zero or an array of zeros, these would imply the sentence has no "top phrases"
            if isinstance(phrase_vec, numpy.ndarray) and any(numpy.zeros(len(phrase_vec)) != phrase_vec):
                just_phrase_vecs.append(list(phrase_vec))
                just_phrase_ids.append(phrase_id)
                just_phrase_text.append(this_text[1])
    return just_phrase_vecs, just_phrase_ids, just_phrase_text

# Cell
def get_optimal_k(just_phrase_vecs, k_range = range(2, 100), save_chart = True, chart_title = "KmeansSilhouette.png"):
    """
    Clusters the top phrase vectors for a range of k values and plots the silhoute coefficients
    (this is a function of mean intra-cluster distance and mean nearest-cluster distance).
    Returns the optimal k-value (highest silhoute coefficient)
    """
    score = [(silhouette_score(just_phrase_vecs, KMeans(i).fit(just_phrase_vecs).predict(just_phrase_vecs))) for i in k_range]
    fig = plt.plot(k_range, score)
    if save_chart:
        plt.savefig(chart_title, dpi=300)
    optimal_k = k_range[score.index(max(score))]
    return optimal_k

def get_cluster_assignments_kmeans(k, just_phrase_vecs):
    "Use K-means algorithm to cluster phr"
    kmeans = KMeans(n_clusters=k, random_state=42).fit(just_phrase_vecs)
    cluster_assignments = kmeans.predict(just_phrase_vecs)
    #TODO: this is never used before being overwritten later. Remove?
    dist = pairwise_distances(just_phrase_vecs, metric='euclidean')
    return cluster_assignments, dist