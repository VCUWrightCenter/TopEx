![CI](https://github.com/AmyOlex/medtop/workflows/CI/badge.svg) 

Documentation is available at https://amyolex.github.io/medtop/.

# MedTop
> Extracting topics from reflective medical writings.


## Requirements
`pip install medtop`

`python -m nltk.downloader all`

## How to use

A template pipeline is provided below using a test dataset. You can read more about the test_data dataset [here](https://github.com/cctrbic/medtop/blob/master/test_data/README.md)

Each step of the pipeline has configuration options for experimenting with various methods. These are detailed in the documentation for each method. Notably, the `import_docs`, `get_cluster_topics`, `visualize_clustering`, and `evaluate` methods all include the option to save results to a file.

## Example Pipeline
### Import data
Import and pre-process documents from a text file containing a list of all documents.

```python
from medtop.core import *
data, doc_df = import_from_files('test_data/corpus_file_list.txt', stop_words_file='stop_words.txt', save_results = False)
```

You can also consolidate your documents into a single, pipe-delimited csv file with the columns "doc_name" and "text".

```python
data, doc_df = import_from_csv('test_data/corpus.txt', stop_words_file='stop_words.txt', save_results = False)
```

### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents. Seed documents can be passed as a single CSV similar to corpus documents in the import step.

NOTE: If `doc_df` is NOT passed to `create_tfidf`, you must set `include_input_in_tfidf=False` in `get_phrases`.

```python
tfidf, dictionary = create_tfidf(doc_df, path_to_seed_topics_file_list='test_data/seed_topics_file_list.txt')
data = get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = True, include_sentiment=True)
data = get_vectors("tfidf", data, dictionary = dictionary, tfidf = tfidf)
```

    Removed 67 sentences without phrases.
    

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics. If you aren't sure how many true clusters exist in the data, try running `assign_clusters` with the optional parameter `show_chart = True` to visual cluster quality with varying numbers of clusters. When using `method='hac'`, you can also use `show_dendrogram = True` see the cluster dendrogram.

```python
data = assign_clusters(data, method = "kmeans", k=4)
cluster_df = get_cluster_topics(data, doc_df, save_results = False)
visualize_clustering(data, method = "svd", show_chart = False)
```

### Evaluate results

```python
gold_file = "test_data/gold.txt"
results_df = evaluate(data, gold_file="test_data/gold.txt", save_results = False)
```

## Document Clustering
**IMPORTANT**: This feature is still in alpha, meaning that we have adapted the pipeline to accomodate the clustering of documents, but have made no rigorous efforts the ensure that it works well.

To cluster documents, simply import data and create the TF-IDF as above, but extract phrase, create the vectors, and cluster using the `doc_df` dataframe. Passing the parameter `window_size=-1` to `get_phrases` tells the method to use all tokens instead of selecting a subset of length `window_size`.

```python
doc_df = get_phrases(doc_df, dictionary.token2id, tfidf, include_input_in_tfidf = True, window_size=-1)
doc_df = get_vectors("tfidf", doc_df, dictionary = dictionary, tfidf = tfidf)
doc_df = assign_clusters(doc_df, method = "kmeans", k=4)
cluster_df = get_cluster_topics(data, doc_df, save_results = False)
visualize_clustering(data, method = "svd", show_chart = False)
```

    Removed 0 sentences without phrases.
    
