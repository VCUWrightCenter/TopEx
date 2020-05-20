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

```
from medtop.core import *
data, doc_df = import_docs('test_data/corpus_file_list.txt', save_results = True)
```

    Results saved to output/DocumentSentenceList.txt
    

### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents.

NOTE: If `doc_df` is NOT passed to `create_tfidf`, you must set `include_input_in_tfidf=False` in `get_phrases`.

```
tfidf, dictionary = create_tfidf(doc_df, 'test_data/seed_topics_file_list.txt')
data = get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = True)
data = get_vectors("tfidf", data, dictionary = dictionary, tfidf = tfidf)
```

    Removed 43 sentences without phrases.
    

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics. If you aren't sure how many true clusters exist in the data, try running `assign_clusters` with the optional parameter `show_chart = True` to visual cluster quality with varying numbers of clusters. When using `method='hac'`, you can also use `show_dendrogram = True` see the cluster dendrogram.

```
data = assign_clusters(data, method = "kmeans", k=4)
cluster_df = get_cluster_topics(data, doc_df, save_results = True)
visualize_clustering(data, method = "svd", show_chart = False)
```

    Results saved to output/TopicClusterResults.txt
    

### Evaluate results

```
gold_file = "test_data/gold.txt"
results_df = evaluate(data, gold_file="test_data/gold.txt", save_results = False)
```
