# AUTOGENERATED! DO NOT EDIT! File to edit: core.ipynb (unless otherwise specified).

__all__ = ['import_data', 'import_from_files', 'import_from_csv', 'create_tfidf', 'get_phrases', 'get_vectors',
           'assign_clusters', 'visualize_clustering', 'get_cluster_topics', 'get_doc_topics', 'evaluate']

# Cell
import gensim
from gensim import corpora, models, matutils
import matplotlib.pyplot as plt
import medtop.internal as internal
import medtop.preprocessing as preprocessing
import numpy as np
import os
import pandas as pd
from pandas import DataFrame, Series
import plotly
import plotly.express as px
from sklearn.manifold import MDS
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import umap.umap_ as umap

# Cell
def import_data(raw_docs:DataFrame, save_results:bool, file_name:str, stop_words_file:str):
    """
    Imports and pre-processes the documents from the `raw_docs` dataframe

    Document pre-processing is handled in [`tokenize_and_stem`](/medtop/preprocessing#tokenize_and_stem).
    `path_to_file_list` is a path to a text file containing a list of files to be processed separated by line breaks.

    Returns (DataFrame, DataFrame)
    """

    # Create a dataframe containing the doc_id, file name, and raw text of each document
    doc_cols = ["id", "doc_name", "text", "tokens"]
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
        internal.sentences_to_disk(data, file_name)

    return data, doc_df

def import_from_files(path_to_file_list:str, save_results:bool = False, file_name:str = 'output/DocumentSentenceList.txt',
               stop_words_file:str = None):
    """
    Imports and pre-processes a list of documents contained in `path_to_file_list`.

    Returns (DataFrame, DataFrame)
    """

    # Extract list of files from the text document
    with open(path_to_file_list, encoding="utf-8") as file:
        file_list = file.read().strip().split('\n')

    docs = []
    for file in file_list:
        # Read documents
        with open(file, encoding="utf-8") as file_content:
            doc_text = file_content.read()
            docs.append(doc_text)

    raw_docs = pd.DataFrame(dict(doc_name=file_list, text=docs))
    data, doc_df = import_data(raw_docs, save_results, file_name, stop_words_file)
    return data, doc_df

def import_from_csv(path_to_csv:str, save_results:bool = False, file_name:str = 'output/DocumentSentenceList.txt',
               stop_words_file:str = None):
    """
    Imports and pre-processes documents from a pipe-demilited csv file. File should be formatted with two columns:
    "doc_name" and "text"

    Returns (DataFrame, DataFrame)
    """
    raw_docs = pd.read_csv(path_to_csv, sep='|')
    data, doc_df = import_data(raw_docs, save_results, file_name, stop_words_file)
    return data, doc_df

# Cell
def create_tfidf(doc_df:DataFrame = None, path_to_seed_topics_file_list:str = None, path_to_seed_topics_csv:str = None):
    """
    Creates a dense TF-IDF matrix from the tokens in the seed topics documents and/or the input corpus.

    `path_to_seed_topics_file_list` is a path to a text file containing a list of files with sentences corresponding to
    known topics. Use the `path_to_seed_topics_csv` if you would prefer to load all seed topics documents from a single,
    pipe-delimited csv file. If the `doc_df` is passed, the input corpus will be used along with the seed topics documents to
    generate the TF-IDF matrix.

    Returns (numpy.ndarray, gensim.corpora.dictionary.Dictionary)
    """
    # Bag of Words (BoW) is a list of all tokens by document
    bow_docs = []

    if doc_df is not None:
        bow_docs = bow_docs + list(doc_df.tokens)

    # Import seed topics documents
    if path_to_seed_topics_file_list is not None:
        _, seed_doc_df = import_from_files(path_to_seed_topics_file_list)
        bow_docs = bow_docs + list(seed_doc_df.tokens)
    elif path_to_seed_topics_csv is not None:
        _, seed_doc_df = import_from_csv(path_to_seed_topics_csv)
        bow_docs = bow_docs + list(seed_doc_df.tokens)

    # Create a dense TF-IDF matrix using document tokens and gensim
    dictionary = corpora.Dictionary(bow_docs)
    corpus = [dictionary.doc2bow(text) for text in bow_docs]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    num_terms = len(corpus_tfidf.obj.idfs)
    tfidf_dense = matutils.corpus2dense(corpus_tfidf, num_terms)

    return tfidf_dense, dictionary

# Cell
def get_phrases(data:DataFrame, feature_names:dict, tdm:np.ndarray, window_size:int = 6,
                include_input_in_tfidf:bool = True):
    """
    Extracts the most expressive phrase from each sentence.

    `feature_names` should be `dictionary.token2id` and `tdm` should be `tfidf` where `dictionary`
    and `tfidf` are output from `create_tfidf`. `window_size` is the length of phrase extracted, if a -1 is passed,
    all tokens will be included (IMPORTANT: this option requires aggregating vectors in the next step.
    When `include_input_in_tfidf` is True, token_scores are calculated using the TF-IDF, otherwise, token_scores
    are calculated using `token_averages`.

    Returns DataFrame
    """
    if window_size > 0:
        token_averages = np.max(tdm, axis=1)

        # Find the most expressive phrase for each sentence and add to dataframe
        lambda_func = lambda sent: internal.get_phrase(sent, window_size, feature_names, include_input_in_tfidf, tdm,
                                                       token_averages)
        phrases = data.apply(lambda_func, axis=1)
        data['phrase'] = phrases
    else:
        data['phrase'] = data.tokens

    # Remove records where phrase is None
    filtered_df = data[data.phrase.notnull()].copy().reset_index(drop=True)
    print(f"Removed {len(data) - len(filtered_df)} sentences without phrases.")

    return filtered_df

# Cell
def get_vectors(method:str, data:DataFrame, dictionary:gensim.corpora.dictionary.Dictionary = None,
                tfidf:np.ndarray = None, dimensions:int = 2, umap_neighbors:int = 15,
                path_to_w2v_bin_file:str = None, doc_df:DataFrame = None):
    """
    Creates a word vector for each phrase in the dataframe.

    Options for `method` are ('tfidf', 'svd', 'umap', 'pretrained', 'local'). Options for `method` are ('tfidf', 'svd', 'umap', 'pretrained', 'local').`tfidf` and `dictionary` are output from
    `create_tfidf`. `dimensions` is the number of dimensions to which SVD or UMAP reduce the TF-IDF matrix.
    `path_to_w2v_bin_file` is the path to a pretrained Word2Vec .bin file.

    Returns DataFrame
    """

    # Create word vectors with TF-IDF
    if method == "tfidf":
        assert dictionary is not None, "Optional parameter: 'dictionary' is required for method: 'tfidf'."
        assert tfidf is not None, "Optional parameter: 'tfidf' is required for method: 'tfidf'."
        lambda_func = lambda sent: internal.get_vector_tfidf(sent, dictionary, tfidf)

    # Create word vectors with SVD transformed TF-IDF
    elif method == "svd":
        assert dictionary is not None, "Optional parameter: 'dictionary' is required for method: 'svd'."
        assert tfidf is not None, "Optional parameter: 'tfidf' is required for method: 'svd'."
        svd =  TruncatedSVD(n_components = dimensions, random_state = 42)
        tfidf_transf = svd.fit_transform(tfidf)
        lambda_func = lambda sent: internal.get_vector_tfidf(sent, dictionary, tfidf_transf)

    # Create word vectors with UMAP transformed TF-IDF
    elif method == "umap":
        assert dictionary is not None, "Optional parameter: 'dictionary' is required for method: 'umap'."
        assert tfidf is not None, "Optional parameter: 'tfidf' is required for method: 'umap'."
        reducer = umap.UMAP(n_neighbors=umap_neighbors, min_dist=.1, metric='cosine', random_state=42, n_components=dimensions)
        embed = reducer.fit_transform(tfidf)
        lambda_func = lambda sent: internal.get_vector_tfidf(sent, dictionary, embed)

    # Create word vectors using a pre-trained Word2Vec model
    elif method == "pretrained":
        assert path_to_w2v_bin_file is not None, "Optional parameter: 'path_to_w2v_bin_file' is required for method: 'pretrained'."
        model = internal.w2v_pretrained(path_to_w2v_bin_file)
        lambda_func = lambda sent: internal.get_vector_w2v(sent, model)

    # Generate a Word2Vec model from the input corpus and use it to create word vectors for each phrase
    elif method == "local":
        assert doc_df is not None, "Optional parameter: 'doc_df' is required for method: 'local'."
        large_sent_vec = list(doc_df.tokens)
        model = models.Word2Vec(sg=1, window = 6, max_vocab_size = None, min_count=1, size=10, iter=500)
        model.build_vocab(large_sent_vec)
        model.train(large_sent_vec, total_examples=model.corpus_count, epochs=model.epochs)
        lambda_func = lambda sent: internal.get_vector_w2v(sent, model)

    # Invalid input paramter
    else:
        raise Exception(f"Unrecognized method: '{method}'")

    # Create a word vector for each phrase and append it to the dataframe
    vectors = data.apply(lambda_func, axis=1)
    data['vec'] = vectors

    return data

# Cell
def assign_clusters(data:DataFrame, method:str = "kmeans", dist_metric:str = "euclidean", k:int = None,
                    height:int = None, show_chart:bool = False, show_dendrogram:bool = False):
    """
    Clusters the sentences using phrase vectors.

    Options for `method` are ('kmeans', 'hac'). Options for `dist_metric` are ('cosine' or anything accepted by
    sklearn.metrics.pairwise_distances). `k` is the number of clusters for K-means clustering. `height` is the height
    at which the HAC dendrogram should be cut. When `show_chart` is True, the chart of silhoute scores by possible k or
    height is shown inline. When `show_dendrogram` is True, the HAC dendrogram is shown inline.

    Returns DataFrame
    """

    # Cluster using K-means algorithm
    if method == "kmeans":
        cluster_assignments = internal.get_clusters_kmeans(data, k, show_chart = show_chart)

    # Cluster using Hierarchical Agglomerative Clustering (HAC)
    elif method == "hac":
        cluster_assignments = internal.get_clusters_hac(data, dist_metric = dist_metric, height = height,
                                                        show_chart = show_chart, show_dendrogram = show_dendrogram)

    # Invalid input parameter
    else:
        raise Exception(f"Unrecognized method: '{method}'")

    data['cluster'] = cluster_assignments
    return data

# Cell
def visualize_clustering(data:DataFrame, method:str = "umap", dist_metric:str = "cosine", umap_neighbors:int = 15,
                         show_chart = True, save_chart = False, return_data = False,
                         chart_file = "output/cluster_visualization.html"):
    """
    Visualize clustering in two dimensions.

    Options for `method` are ('umap', 'mds', 'svd'). Options for `dist_metric` are ('cosine' or anything accepted by
    sklearn.metrics.pairwise_distances). When `show_chart` is True, the visualization is shown inline.
    When `save_chart` is True, the visualization is saved to `chart_file`.

    Returns DataFrame
    """

    # Calculate distances between all pairs of phrases
    dist = pairwise_distances(list(data.vec), metric=dist_metric)

    # Visualize the clusters using UMAP
    if method == "umap":
        reducer = umap.UMAP(n_neighbors=umap_neighbors, min_dist=.1, metric='cosine', random_state=42)
        embedding = reducer.fit_transform(dist)
        x, y = embedding[:, 0], embedding[:, 1]

    # Visualize the clusters using Multi-Dimensional Scaling (MDS)
    elif method == "mds":
        mds = MDS(n_components=2, dissimilarity="precomputed", random_state=42)
        pos = mds.fit_transform(dist)
        x, y = pos[:, 0], pos[:, 1]

    # Visualize the clusters using Singular Value Decomposition (SVD)
    elif method == "svd":
        svd2d =  TruncatedSVD(n_components = 2, random_state = 42).fit_transform(dist)
        x, y = svd2d[:, 0], svd2d[:, 1]

    # Invalid input parameter
    else:
        raise Exception(f"Unrecognized method: '{method}'")

    visualization_df = DataFrame(dict(label=list(data.id), cluster=list(data.cluster), phrase=list(data.phrase),
                                      text=list(data.text), x=x, y=y))

    # To keep the visualization legible, limit
    max_phrase = 10
    vis_df = visualization_df.copy()
    vis_df.phrase = vis_df.apply(lambda x: x.phrase[:max_phrase] + ['...'] if len(x.phrase)>max_phrase else x.phrase, axis=1)
    fig = px.scatter(vis_df, x="x", y="y", hover_name="label", color="cluster", hover_data=["phrase","cluster"],
                         color_continuous_scale='rainbow')

    # Print visualization to screen by default
    if show_chart:
        fig.show()

    # Optionally save the chart to a file
    if save_chart:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(chart_file), exist_ok=True)

        plotly.offline.plot(fig, filename=chart_file)

    # Return the data to display clusters
    if return_data:
        return visualization_df

# Cell
def get_cluster_topics(data:DataFrame, doc_df:DataFrame = None, topics_per_cluster:int = 10, save_results:bool = False,
                       file_name:str = 'output/TopicClusterResults.txt'):
    """
    Gets the main topics for each cluster.

    `topics_per_cluster` is the number of main topics per cluster. When `save_results` is True, the resulting dataframe
    will be saved to `file_name`.

    Returns DataFrame
    """

    # Iterate distinct clusters
    rows = []
    for c in set(data.cluster):
        cluster_tokens = [t for t in data[data.cluster == c].tokens]
        topics = internal.get_topics_from_docs(cluster_tokens, topics_per_cluster)
        rows.append(Series([c, topics, len(cluster_tokens)], index=["cluster", "topics", "sent_count"]))

    cluster_df = DataFrame(rows)

    # Optionally save clusters to disk
    if save_results:
        assert doc_df is not None, "Optional parameter: 'doc_df' is required when save_results = True."
        internal.clusters_to_disk(data, doc_df, cluster_df, file_name)

    return cluster_df

# Cell
def get_doc_topics(doc_df:DataFrame, topics_per_doc:int = 10, save_results:bool = False,
                       file_name:str = 'output/TopicDocumentResults.txt'):
    """
    Gets the main topics for each document.

    `topics_per_doc` is the number of topics extracted per document. When `save_results` is True, the resulting dataframe
    will be saved to `file_name`.

    Returns DataFrame
    """
    doc_df['topics'] = [internal.get_topics_from_docs([doc], topics_per_doc) for doc in doc_df.tokens]

    # Optionally save clusters to disk
    if save_results:
        internal.df_to_disk(doc_df, file_name)

    return doc_df

# Cell
def evaluate(data, gold_file, save_results = False, file_name = "output/EvaluationResults.txt"):
    """
    Evaluate precision, recall, and F1 against a gold standard dataset.

    `gold_file` is a path to a text file containing a list IDs and labels. When `save_results` is True, the resulting
    dataframe will be saved to `file_name`.

    Returns DataFrame
    """

    # Import gold standard list of IDs (doc.#.sent.#) and labels
    gold_df = pd.read_csv(gold_file, names=["id", "label"], sep="\t", encoding="utf-8")

    # Inner join the actual labels with the assigned clusters for each document.
    eval_df = pd.merge(gold_df, data[["id", "cluster"]], on="id")

    # Iterate labels in the gold standard dataset
    rows = []
    for label in set(gold_df.label):
        cluster_rows = eval_df[eval_df.label == label]

        # Find the cluster with the most instances of each label in the gold standard dataset
        closest_cluster = cluster_rows.cluster.mode()[0] if len(cluster_rows) > 0 else -1

        # IDs assigned to a label in the gold standard dataset
        gold_examples = set(gold_df[gold_df.label == label].id)

        # IDs in the closest cluster
        closest_cluster_members = set(eval_df[eval_df.cluster == closest_cluster].id)

        # Calculate performance metrics
        tp = len(gold_examples.intersection(closest_cluster_members))
        fp = len(closest_cluster_members - gold_examples)
        fn = len(gold_examples - closest_cluster_members)
        precision = round(tp/(tp+fp), 3) if (tp+fp) > 0 else float("Nan")
        recall = round(tp/(tp+fn), 3) if (tp+fn) > 0 else float("Nan")
        f1 = round(2*((precision*recall)/(precision+recall)), 3) if (precision+recall) > 0 else float("Nan")

        rows.append(Series([label, gold_examples, closest_cluster, closest_cluster_members, tp, fp, fn, precision, recall, f1],
                              index=["label", "gold_examples", "closest_cluster", "closest_cluster_members", "tp", "fp", "fn", "precision", "recall", "f1"]))

    # Create results dataframe with a row for each label
    results_df = DataFrame(rows).sort_values(by=["label"])

    # Optionally save the results to disk
    if save_results:
        internal.df_to_disk(results_df, file_name)

    return results_df