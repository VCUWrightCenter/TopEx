# AUTOGENERATED! DO NOT EDIT! File to edit: core.ipynb (unless otherwise specified).

__all__ = ['import_docs', 'create_tfidf', 'get_phrases', 'get_vectors', 'assign_clusters', 'visualize_clustering',
           'get_cluster_topics', 'evaluate']

# Cell
from gensim import corpora, models, matutils
import matplotlib.pyplot as plt
import medtop.internal as internal
import medtop.preprocessing as preprocessing
import numpy as np
import pandas as pd
import plotly
import plotly.express as px
from sklearn.manifold import MDS
from sklearn.metrics import silhouette_score, pairwise_distances
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import umap.umap_ as umap

# Cell
def import_docs(path_to_file_list, save_results = False, file_name = 'output/DocumentSentenceList.txt'):
    "Imports and preprocesses the list of documents contained in the input file."

    # Extract list of files from text document
    with open(path_to_file_list, encoding="utf-8") as file:
        file_list = file.read().strip().split('\n')

    # Create a dataframe containing the doc_id, file name, and raw text of each document
    doc_cols = ["doc_id", "file", "text", "tokens"]
    doc_rows = []

    # Create a dataframe containing the id, doc_id, sent_id, raw text, tokens, and PoS tags for each sentence
    data_cols = ["id", "doc_id", "sent_id", "text", "tokens", "pos_tags"]
    data_rows = []

    for doc_id, file in enumerate(file_list):
        # Read document
        with open(file, encoding="utf-8") as file_content:
            doc_text = file_content.read()

        # Pre-process document into cleaned sentences
        sent_tokens, sent_pos, raw_sent = preprocessing.tokenize_and_stem(doc_text)

        # Populate a row in data for each sentence in the document
        for sent_id, _ in enumerate(sent_tokens):
            row_id = f"doc.{doc_id}.sent.{sent_id}"
            sent_text = raw_sent[sent_id]
            tokens = sent_tokens[sent_id]
            pos_tags = sent_pos[sent_id]
            data_rows.append(pd.Series([row_id, doc_id, sent_id, sent_text, tokens, pos_tags], index=data_cols))

        # Populate a row in doc_df for each file loaded
        doc_tokens = [token for sent in sent_tokens for token in sent]
        doc_row = pd.Series([doc_id, file, doc_text, doc_tokens], index=doc_cols)
        doc_rows.append(doc_row)

    # Create dataframes from lists of Series
    data = pd.DataFrame(data_rows)
    doc_df = pd.DataFrame(doc_rows)

    # Optionally save the results to disk
    if save_results:
        internal.sentences_to_disk(data, file_name)

    return data, doc_df

# Cell
def create_tfidf(path_to_seed_topics_file_list, input_doc_df = None):
    "Create a TF-IDF matrix from the tokens in the seed topics documents and optionally, the input corpus"

    # Import seed topics documents
    _, seed_doc_df = import_docs(path_to_seed_topics_file_list)

    # Bag of Words (BoW) is a list of all tokens by document
    bow_docs = list(seed_doc_df.tokens)

    if input_doc_df is not None:
        bow_docs = bow_docs + list(input_doc_df.tokens)

    # Create a dense TF-IDF matrix using document tokens and gensim
    dictionary = corpora.Dictionary(bow_docs)
    corpus = [dictionary.doc2bow(text) for text in bow_docs]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = tfidf[corpus]
    num_terms = len(corpus_tfidf.obj.idfs)
    tfidf_dense = matutils.corpus2dense(corpus_tfidf, num_terms)

    return tfidf_dense, dictionary

# Cell
def get_phrases(data, feature_names, tdm, window_size = 6, include_input_in_tfidf = False):
    """
    Extracts the most expressive phrase of length `window_size` from each sentence and appends them to the input dataframe in a new 'phrase' column.
    Sentences without phrases of sufficient length are removed.
    """

    # TODO: Clarify this
    if not include_input_in_tfidf:
        token_averages = np.max(tdm, axis=1)

    # Find the most expressive phrase for each sentence and add to dataframe
    lambda_func = lambda sent: internal.get_phrase(sent, window_size, feature_names, include_input_in_tfidf, tdm, token_averages)
    phrases = data.apply(lambda_func, axis=1)
    data['phrase'] = phrases

    # Remove records where phrase is None
    filtered_df = data[data.phrase.notnull()].copy().reset_index(drop=True)
    print(f"Removed {len(data) - len(filtered_df)} sentences without phrases.")

    return filtered_df

# Cell
def get_vectors(method, data, dictionary = None, tfidf = None, dimensions = 2, umap_neighbors = 15, path_to_w2v_bin_file = None, doc_df = None):
    "Creates a word vector for each phrase in the dataframe."

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
def assign_clusters(data, method = "kmeans", dist_metric = "euclidean", k = None, height = None, show_chart = False, show_dendrogram = False):
    "Clusters the sentences using phrase vectors."

    # Cluster using K-means algorithm
    if method == "kmeans":
        cluster_assignments = internal.get_cluster_assignments_kmeans(data, k, show_chart = show_chart)

    # Cluster using Hierarchical Agglomerative Clustering (HAC)
    elif method == "hac":
        cluster_assignments = internal.get_cluster_assignments_hac(data, dist_metric = dist_metric, height = height, show_chart = show_chart, show_dendrogram = show_dendrogram)

    # Invalid input parameter
    else:
        raise Exception(f"Unrecognized method: '{method}'")

    data['cluster'] = cluster_assignments
    return data

# Cell
def visualize_clustering(data, method = "umap", dist_metric = "cosine", umap_neighbors = 15, display_inline = True, save_chart = False, chart_file = "cluster_visualization.html"):
    "Visualize clustering in two dimensions."

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

    # Print visualization to screen by default
    if display_inline:
        visualization_df = pd.DataFrame(dict(id=list(data.id), cluster=list(data.cluster), phrase=list(data.phrase), x=x, y=y))
        fig = px.scatter(visualization_df, x="x", y="y", hover_name="id", color="cluster", hover_data=["phrase","cluster"], color_continuous_scale='rainbow')
        fig.show()

    # Optionally save the chart to a file
    if save_chart:
        plotly.offline.plot(fig, filename=chart_file)

# Cell
def get_cluster_topics(data, doc_df = None, topics_per_cluster = 10, save_results = False, file_name = 'output/TopicClusterResults.txt'):
    "Returns a dataframe containing a list of the main topics for each cluster."

    # Iterate distinct clusters
    rows = []
    for c in set(data.cluster):
        cluster_tokens = [t for t in data[data.cluster == c].tokens]
        dictionary = corpora.Dictionary(cluster_tokens)
        corpus = [dictionary.doc2bow(text) for text in cluster_tokens]

        # Use Latent Dirichlet Allocation (LDA) to find the main topics
        lda = models.LdaModel(corpus, num_topics=1, id2word=dictionary)
        topics_matrix = lda.show_topics(formatted=False, num_words=topics_per_cluster)
        topics = list(np.array(topics_matrix[0][1])[:,0])
        rows.append(pd.Series([c, topics, len(cluster_tokens)], index=["cluster", "topics", "sent_count"]))

    cluster_df = pd.DataFrame(rows)

    # Optionally save clusters to disk
    if save_results:
        assert doc_df is not None, "Optional parameter: 'doc_df' is required when save_results = True."
        internal.clusters_to_disk(data, doc_df, cluster_df, file_name)

    return cluster_df

# Cell
def evaluate(data, gold_file, save_results = False, file_name = "output/EvaluationResults.txt"):
    "Evaluate precision, recall, and F1 against a gold standard dataset."

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

        rows.append(pd.Series([label, gold_examples, closest_cluster, closest_cluster_members, tp, fp, fn, precision, recall, f1],
                              index=["label", "gold_examples", "closest_cluster", "closest_cluster_members", "tp", "fp", "fn", "precision", "recall", "f1"]))

    # Create results dataframe with a row for each label
    results_df = pd.DataFrame(rows).sort_values(by=["label"])

    # Optionally save the results to disk
    if save_results:
        internal.df_to_disk(results_df, file_name)

    return results_df