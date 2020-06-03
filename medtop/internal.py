# AUTOGENERATED! DO NOT EDIT! File to edit: internal.ipynb (unless otherwise specified).

__all__ = ['import_data', 'get_phrase', 'get_vector_tfidf', 'get_vector_w2v', 'w2v_pretrained',
           'get_silhouette_score_hac', 'get_tree_height', 'get_linkage_matrix', 'get_optimal_height',
           'get_clusters_hac', 'get_silhouette_score_kmeans', 'get_optimal_k', 'get_clusters_kmeans',
           'get_topics_from_docs', 'df_to_disk', 'sentences_to_disk', 'write_cluster', 'clusters_to_disk']

# Cell
import csv
import gensim
from gensim import corpora, models
import matplotlib.pyplot as plt
import medtop.preprocessing as preprocessing
import numpy as np
import os
import pandas as pd
from pandas import DataFrame, Series
from scipy.cluster import hierarchy
from scipy.cluster.hierarchy import ward, cut_tree, dendrogram
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob

# Cell
def import_data(raw_docs:DataFrame, save_results:bool, file_name:str, stop_words_file:str):
    """
    Imports and pre-processes the documents from the `raw_docs` dataframe

    Document pre-processing is handled in [`tokenize_and_stem`](/medtop/preprocessing#tokenize_and_stem).
    `path_to_file_list` is a path to a text file containing a list of files to be processed separated by line breaks.

    Returns (DataFrame, DataFrame)
    """

    # Create a dataframe containing the doc_id, file name, and raw text of each document
    doc_cols = ["doc_id", "doc_name", "text", "tokens"]
    doc_rows = []

    # Create a dataframe containing the id, doc_id, sent_id, raw text, tokens, and PoS tags for each sentence
    data_cols = ["id", "doc_id", "sent_id", "text", "tokens", "pos_tags"]
    data_rows = []

    for doc_id in range(len(raw_docs)):
        doc = raw_docs.iloc[doc_id]

        # Pre-process document into cleaned sentences
        sent_tokens, sent_pos, raw_sent = preprocessing.tokenize_and_stem(doc.text, stop_words_file=stop_words_file)

        # Populate a row in data for each sentence in the document
        for sent_id, _ in enumerate(sent_tokens):
            row_id = f"doc.{doc_id}.sent.{sent_id}"
            sent_text = raw_sent[sent_id]
            tokens = sent_tokens[sent_id]
            pos_tags = sent_pos[sent_id]
            data_rows.append(Series([row_id, doc_id, sent_id, sent_text, tokens, pos_tags], index=data_cols))

        # Populate a row in doc_df for each file loaded
        doc_tokens = [token for sent in sent_tokens for token in sent]
        doc_row = Series([doc_id, doc.doc_name, doc.text, doc_tokens], index=doc_cols)
        doc_rows.append(doc_row)

    # Create dataframes from lists of Series
    data = DataFrame(data_rows)
    doc_df = DataFrame(doc_rows)

    # Optionally save the results to disk
    if save_results:
        sentences_to_disk(data, file_name)

    return data, doc_df

# Cell
def get_phrase(sent:Series, window_size:int, feature_names:dict, include_input_in_tfidf:bool, tdm:np.ndarray,
               token_averages:np.ndarray):
    """
    Finds the most expressive phrase in a sentence. This function is called in a lambda expression in `core.get_phrases`.

    Returns list
    """
    adj_adv_pos_list = ["JJ","JJR", "JJS", "RB", "RBR", "RBS"]
    phrase_scores = []
    top_phrase = None
    top_score = -1

    # Iterate phrases (sub-sentences of length window_size)
    for p in range(len(sent.tokens) - window_size + 1):
        window = slice(p, p + window_size)
        phrase = sent.tokens[window]
        phrase_pos = sent.pos_tags[window]

        weight = 1 + abs(TextBlob(" ".join(phrase)).sentiment.polarity)
        score = 0

        for i, token in enumerate(phrase):
            # Skip tokens not in feature_names
            if token not in list(feature_names.keys()):
                continue

            pos = phrase_pos[i][1]
            token_ix = feature_names[token]

            # Token score comes from TF-IDf matrix if include_input_in_tfidf is set, otherwise, use tokens averages
            token_score = tdm[token_ix, sent.doc_id] if include_input_in_tfidf else token_averages[token_ix];

            # Scale token_score by 3x if the token is an adjective or adverb
            score += (token_score * 3) if pos in adj_adv_pos_list else token_score

        # Update top_score if necessary
        phrase_score = score * weight
        if phrase_score > top_score:
            top_phrase = phrase
            top_score = phrase_score

    return top_phrase

# Cell
def get_vector_tfidf(sent:Series, dictionary:gensim.corpora.dictionary.Dictionary, term_matrix:np.ndarray):
    """
    Create a word vector for a given sentence using a term matrix.
    This function is called in a lambda expression in `core.get_vectors`.

    Returns list
    """
    vec_ids = [x[0] for x in dictionary.doc2bow(sent.phrase)]
    return term_matrix[vec_ids].sum(axis=0)

def get_vector_w2v(sent:Series, model:gensim.models.keyedvectors.Word2VecKeyedVectors):
    """
    Create a word vector for a given sentence using a Word2Vec model.
    This function is called in a lambda expression in `core.get_vectors`.

    Returns list
    """
    tokens = [token for token in sent.phrase if token in model.wv.vocab]
    return model[tokens].sum(axis=0)

# Cell
def w2v_pretrained(bin_file:str):
    """
    Load a pre-trained Word2Vec model from a bin file.

    Returns gensim.models.keyedvectors.Word2VecKeyedVectors
    """
    return gensim.models.KeyedVectors.load_word2vec_format(bin_file, binary=True)

# Cell
def get_silhouette_score_hac(phrase_vecs:list, linkage_matrix:np.ndarray, height:int):
    """
    Assigns clusters to a list of word vectors for a given `height` and calculates the silhouette score of the clustering.

    Returns float
    """
    cluster_assignments = [x[0] for x in cut_tree(linkage_matrix, height=height)]
    return silhouette_score(phrase_vecs, cluster_assignments)

def get_tree_height(root:hierarchy.ClusterNode):
    """
    Gets the height of a binary tree.

    Returns int
    """
    if root is None:
        return 1
    return max(get_tree_height(root.left), get_tree_height(root.right)) + 1

def get_linkage_matrix(phrase_vecs:list, dist_metric:str):
    """
    Creates a linkage matrix by calculating distance between phrase vectors.

    Returns np.ndarray
    """
    if dist_metric == "cosine":
        dist = 1 - cosine_similarity(phrase_vecs)
    else:
        dist = pairwise_distances(phrase_vecs, metric=dist_metric)
    return ward(dist)

def get_optimal_height(data:DataFrame, linkage_matrix:np.ndarray, show_dendrogram:bool = False, show_chart:bool = True,
                       save_chart:bool = False, chart_file:str = "HACSilhouette.png"):
    """
    Clusters the top phrase vectors and plots the silhoute coefficients for a range of dendrograph heights.
    Returns the optimal height value (highest silhoute coefficient)

    Returns int
    """
    # Maximum cut point height is the height of the tree
    max_h = get_tree_height(hierarchy.to_tree(linkage_matrix)) + 1
    h_range = range(2,max_h)
    phrase_vecs = list(data.vec)
    h_scores = [get_silhouette_score_hac(phrase_vecs, linkage_matrix, h) for h in h_range]

    # Optionally display the clustering dendrogram
    if show_dendrogram:
        dendrogram(linkage_matrix)
        plt.show()

    # Optionally display the graph of silhouette score by height
    if show_chart:
        fig = plt.plot(h_range, h_scores)
        plt.show()

    # Optionally save the graph of silhouette score by height to disk
    if save_chart:
        plt.savefig(chart_file, dpi=300)

    # optimal_h is height value with the highest silhouette score
    optimal_height = h_range[np.argmax(h_scores)]
    return optimal_height

def get_clusters_hac(data:DataFrame, dist_metric:str, height:int = None, show_dendrogram:bool = False,
                     show_chart:bool = False):
    """
    Use Hierarchical Agglomerative Clustering (HAC) to cluster phrase vectors

    Returns list
    """
    linkage_matrix = get_linkage_matrix(list(data.vec), dist_metric)

    # Use optimal height if no height is specified
    if height is None:
        height = get_optimal_height(data, linkage_matrix, show_dendrogram, show_chart)

    cluster_assignments = [x[0] for x in cut_tree(linkage_matrix, height=height)]
    return cluster_assignments

# Cell
def get_silhouette_score_kmeans(phrase_vecs:list, k:int):
    """
    Assigns clusters to a list of word vectors for a given `k` and calculates the silhouette score of the clustering.

    Returns float
    """
    cluster_assignments = KMeans(k).fit(phrase_vecs).predict(phrase_vecs)
    return silhouette_score(phrase_vecs, cluster_assignments)

def get_optimal_k(data:DataFrame, show_chart:bool = True, save_chart:bool = False,
                  chart_file:str = "KmeansSilhouette.png"):
    """
    Calculates the optimal k-value (highest silhoute coefficient).
    Optionally prints a chart of silhouette score by k-value or saves it to disk.

    Returns int
    """
    phrase_vecs = list(data.vec)
    max_k = min(len(phrase_vecs), 100)
    k_range = range(2, max_k)
    score = [get_silhouette_score_kmeans(phrase_vecs, i) for i in k_range]

    # Optionally display the graph of silhouette score by k-value
    if show_chart:
        fig = plt.plot(k_range, score)

    # Optionally save the graph of silhouette score by k-value to disk
    if save_chart:
        plt.savefig(chart_file, dpi=300)

    # optimal_k is k value with the highest silhouette score
    optimal_k = k_range[np.argmax(score)]
    return optimal_k

def get_clusters_kmeans(data:DataFrame, k:int = None, show_chart:bool = False):
    """
    Use K-means algorithm to cluster phrase vectors

    Returns list
    """
    phrase_vecs = list(data.vec)

    # Use optimal k if no k-value is specified
    if k is None:
        k = get_optimal_k(data, show_chart)

    # Assign clusters
    kmeans = KMeans(n_clusters=k, random_state=42).fit(phrase_vecs)
    cluster_assignments = kmeans.predict(phrase_vecs)

    return cluster_assignments

# Cell
def get_topics_from_docs(docs:list, topic_count:int):
    """
    Gets a list of `topic_count` topics for each list of tokens in `docs`.

    Returns list
    """
    dictionary = corpora.Dictionary(docs)
    corpus = [dictionary.doc2bow(text) for text in docs]

    # Use Latent Dirichlet Allocation (LDA) to find the main topics
    lda = models.LdaModel(corpus, num_topics=1, id2word=dictionary)
    topics_matrix = lda.show_topics(formatted=False, num_words=topic_count)
    topics = list(np.array(topics_matrix[0][1])[:,0])
    return topics

# Cell
def df_to_disk(df:DataFrame, file_name:str, mode:str="w", header:bool=True, sep='\t'):
    """
    Writes a dataframe to disk as a tab delimited file.

    Returns None
    """
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    df.to_csv(file_name, sep=sep, mode=mode, header=header, encoding='utf-8', index=False, quoting=csv.QUOTE_NONE, quotechar="",  escapechar="\\")
    if mode == "w":
        print(f"Results saved to {file_name}")

def sentences_to_disk(data:DataFrame, file_name:str = 'output/DocumentSentenceList.txt'):
    """
    Writes the raw sentences to a file organized by document and sentence number.

    Returns None
    """
    df = data[["id", "text"]].copy()
    df_to_disk(df, file_name)


def write_cluster(cluster_rows:DataFrame, file_name:str, mode:str = 'a', header:bool=False):
    """
    Appends the rows for a single cluster to disk.

    Returns None
    """
    df_to_disk(cluster_rows, file_name, mode=mode, header=header)


def clusters_to_disk(data:DataFrame, doc_df:DataFrame, cluster_df:DataFrame,
                     file_name:str = 'output/TopicClusterResults.txt'):
    """
    Writes the sentences and phrases to a file organized by cluster and document.

    Returns None
    """
    # Create a dataframe containing the data to be saved to disk
    df = data[["cluster", "doc_id", "sent_id", "text", "phrase"]].copy()
    doc_names = [doc_df.loc[c].doc_name for c in data.doc_id]
    df.insert(loc=3, column='doc_name', value=doc_names)
    df.sort_values(by=["cluster", "doc_id", "sent_id"], inplace=True)

    # Write document header
    cluster_rows = pd.DataFrame(None, columns=df.columns)
    write_cluster(cluster_rows, file_name, mode = 'w', header=True)

    # Write each cluster
    for c in set(data.cluster):
        # Write a cluster header containing the main topics for each cluster
        with open(file_name, encoding="utf-8", mode = 'a') as file:
            keywords = ', '.join(cluster_df.loc[c, 'topics'])
            file.write(f"Cluster: {c}; Keywords: [{keywords}]\n")

        # Write the sentences in each cluster
        cluster_rows = df[df.cluster == c].copy()
        write_cluster(cluster_rows, file_name)