# AUTOGENERATED! DO NOT EDIT! File to edit: internal.ipynb (unless otherwise specified).

__all__ = ['get_cluster_sent_coords', 'set_phrase_column', 'set_vec_column_tfidf', 'set_vec_column_w2v',
           'get_silhouette_score_hac', 'get_tree_height', 'get_linkage_matrix', 'get_optimal_height',
           'get_cluster_assignments_hac', 'get_silhouette_score_kmeans', 'get_optimal_k',
           'get_cluster_assignments_kmeans']

# Cell
from nbdev.imports import *
from nbdev.export import *
import numpy as np
from scipy.cluster import hierarchy
from scipy.cluster.hierarchy import ward, cut_tree, dendrogram
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, pairwise_distances
from textblob import TextBlob

# Cell
#DELETE
def get_cluster_sent_coords(cluster_id, just_phrase_ids, cluster_assignments):
    "Parse (doc_id, sent_id) 'coordinate' pairs"
    #QUESTION: I removed the condition len(x.split(".")) > 1 is there a case when that wouldn't be True?
    cluster_mask = np.asarray(cluster_assignments) == cluster_id
    # TODO: Consolidate the next two lines if Amy's okay with storing just_phrase_ids as a list of tuples
    topic_labels = np.asarray(just_phrase_ids)[cluster_mask]
    sent_coords = [[int(x.split(".")[1]), int(x.split(".")[3])] for x in topic_labels]
    return sent_coords

# Cell
def set_phrase_column(sent, window_size, feature_names, include_input_in_tfidf, tdm, token_averages):
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

    sent.phrase = top_phrase
    return sent

# Cell
def set_vec_column_tfidf(sent, dictionary, term_matrix):
    "Lambda function for setting the vec column to be applied to each row in a dataframe"
    if sent.phrase is not None:
        vec_ids = [x[0] for x in dictionary.doc2bow(sent.phrase)]
        sent.vec = term_matrix[vec_ids].sum(axis=0)
    return sent

def set_vec_column_w2v(sent, model):
    "Lambda function for setting the vec column to be applied to each row in a dataframe"
    if sent.phrase is not None:
        tokens = [token for token in sent.phrase if token in model.wv.vocab]
        sent.vec = model[tokens].sum(axis=0)
    return sent

# Cell
def get_silhouette_score_hac(phrase_vecs, linkage_matrix, height):
    "Assigns clusters to a list of word vectors for a given `height` and calculates the silhouette score of the clustering."
    cluster_assignments = [x[0] for x in cut_tree(linkage_matrix, height=height)]
    return silhouette_score(phrase_vecs, cluster_assignments)

def get_tree_height(root):
    "Gets the height of a binary tree."
    if root is None:
        return 1
    return max(get_tree_height(root.left), get_tree_height(root.right)) + 1

def get_linkage_matrix(phrase_vecs, dist_metric):
    "Creates a linkage matrix by calculating distance between phrase vectors."
    if dist_metric == "cosine":
        dist = 1 - cosine_similarity(phrase_vecs)
    else:
        dist = pairwise_distances(phrase_vecs, metric=dist_metric)
    return ward(dist)

def get_optimal_height(data, linkage_matrix, show_dendrogram = False, show_chart = True, save_chart = False, chart_file = "HACSilhouette.png"):
    """
    Clusters the top phrase vectors and plots the silhoute coefficients for a range of dendrograph heights.
    Returns the optimal height value (highest silhoute coefficient)
    """
    phrase_vecs = list(data.vec)
    max_h = get_tree_height(hierarchy.to_tree(linkage_matrix)) + 1
    h_range = range(2,max_h)
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

def get_cluster_assignments_hac(data, dist_metric, height = None, show_dendrogram = False, show_chart = False):
    "Use Hierarchical Agglomerative Clustering (HAC) to cluster phrase vectors"
    linkage_matrix = get_linkage_matrix(list(data.vec), dist_metric)

    # Use optimal height if no height is specified
    if height is None:
        height = get_optimal_height(data, linkage_matrix, show_dendrogram, show_chart)

    cluster_assignments = [x[0] for x in cut_tree(linkage_matrix, height=height)]
    return cluster_assignments

# Cell
def get_silhouette_score_kmeans(phrase_vecs, k):
    "Assigns clusters to a list of word vectors for a given `k` and calculates the silhouette score of the clustering."
    cluster_assignments = KMeans(k).fit(phrase_vecs).predict(phrase_vecs)
    return silhouette_score(phrase_vecs, cluster_assignments)

def get_optimal_k(data, show_chart = True, save_chart = False, chart_file = "KmeansSilhouette.png"):
    "Calculates the optimal k-value (highest silhoute coefficient). Optionally prints a chart of silhouette score by k-value or saves it to disk."
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

def get_cluster_assignments_kmeans(data, k = None, show_chart = False):
    "Use K-means algorithm to cluster phrase vectors"
    phrase_vecs = list(data.vec)

    # Use optimal k if no k-value is specified
    if k is None:
        k = get_optimal_k(data, show_chart)

    # Assign clusters
    kmeans = KMeans(n_clusters=k, random_state=42).fit(phrase_vecs)
    cluster_assignments = kmeans.predict(phrase_vecs)

    return cluster_assignments