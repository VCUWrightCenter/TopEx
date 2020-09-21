![CI](https://github.com/VCUWrightCenter/TopEx/workflows/CI/badge.svg) 

Documentation is available at https://VCUWrightCenter.github.io/TopEx/.

# TopEx
> Topic exploration in unstructured text documents.


## Requirements
TopEx is only compatible with 64-bit python. You can check which version of python you're using in your virtual environment with the following code.

`import platform; platform.architecture()[0];`

`pip install topex`

## How to use

A template pipeline is provided below using a test dataset. You can read more about the test_data dataset [here](https://github.com/VCUWrightCenter/TopEx/tree/master/test_data/README.md)

Each step of the pipeline has configuration options for experimenting with various methods. These are detailed in the documentation for each method. Notably, the `import_docs`, `get_cluster_topics`, `visualize_clustering`, and `evaluate` methods all include the option to save results to a file.

## Example Pipeline
### Import data
Import and pre-process documents from a text file containing a list of all documents.

```python
import topex.core as topex
data, doc_df = topex.import_from_files('test_data/corpus_file_list.txt', stop_words_file='stop_words.txt', save_results = False)
```

You can also consolidate your documents into a single, pipe-delimited csv file with the columns "doc_name" and "text".

```python
data, doc_df = topex.import_from_csv('test_data/corpus.txt', stop_words_file='stop_words.txt', save_results = False)
```

### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents. Seed documents can be passed as a single CSV similar to corpus documents in the import step.

NOTE: If `doc_df` is NOT passed to `create_tfidf`, you must set `include_input_in_tfidf=False` in `get_phrases`.

```python
tfidf, dictionary = topex.create_tfidf(doc_df, path_to_seed_topics_file_list='test_data/seed_topics_file_list.txt')
data = topex.get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = True, include_sentiment=True)
data = topex.get_vectors("svd", data, dictionary = dictionary, tfidf = tfidf, dimensions=min(200,tfidf.shape[1]-1))
```

    Removed 67 sentences without phrases.
    

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics. If you aren't sure how many true clusters exist in the data, try running `assign_clusters` with the optional parameter `show_chart = True` to visual cluster quality with varying numbers of clusters. When using `method='hac'`, you can also use `show_dendrogram = True` see the cluster dendrogram.

```python
data, linkage_matrix, max_height, height = topex.assign_clusters(data, method = "hac", show_chart = False)
viz_df = topex.visualize_clustering(data, method="umap", show_chart=False, return_data=True)
```

### Cluster size exploration
Determining the correct number of clusters can often be as much art as science, so we've included a mechanism to 
quickly iterate through various values of `k` or cut heights for the HAC tree. Mapping the data points into the x,y coordinate plane need only be performed once as it depends solely on the vector representation of each sentence and the `visualize_clustering` method returns those values in a dataframe, which can be used to quickly redraw the visualization after updating cluster assignments using a different `k` or `height`. Similarly, computing the tree for HAC clustering can be done once and then cut at different heights to produce different clusters. `assign_clusters` returns the `linkage_matrix` and `max_height` at which you can cut the tree.

Use the `recluster` method to experiment with different values of `k` or `height`. You can also, remove noise from the visualization by setting the `min_cluster_size` parameter. This only hides points from the visualization and does not remove them from `data`.

```python
# data, cluster_df = topex.recluster(data, viz_df, cluster_method='kmeans', k=25, min_cluster_size=6, show_chart=False)
data, cluster_df = topex.recluster(data, viz_df, linkage_matrix=linkage_matrix, cluster_method='hac', height=height+1, 
                                   min_cluster_size=5, show_chart=False)
```

### Evaluate results

```python
gold_file = "test_data/gold.txt"
cluster_df = topex.get_cluster_topics(data, doc_df, save_results = False)
results_df = topex.evaluate(data, gold_file="test_data/gold.txt", save_results = False)
```

## Document Clustering
**IMPORTANT**: This feature is still in alpha, meaning that we have adapted the pipeline to accomodate the clustering of documents, but have made no rigorous efforts the ensure that it works well.

To cluster documents, simply import data and create the TF-IDF as above, but extract phrase, create the vectors, and cluster using the `doc_df` dataframe. Passing the parameter `window_size=-1` to `get_phrases` tells the method to use all tokens instead of selecting a subset of length `window_size`.

```python
doc_df = topex.get_phrases(doc_df, dictionary.token2id, tfidf, include_input_in_tfidf = True, window_size=-1)
doc_df = topex.get_vectors("svd", doc_df, dictionary = dictionary, tfidf = tfidf)
doc_df = topex.assign_clusters(doc_df, method = "kmeans", k=4)
cluster_df = topex.get_cluster_topics(data, doc_df, save_results = False)
topex.visualize_clustering(data, method = "umap", show_chart = False)
```

    Removed 0 sentences without phrases.
    
