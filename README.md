![CI](https://github.com/cctrbic/medtop/workflows/CI/badge.svg)
# MedTop
> Extracting topics from reflective medical writings.  


```python
# all_flag
# Exempt this notebook from being run during GitHub CI.
```

## Requirements
`pip install medtop`  

`python -m nltk.downloader all`

## How to use

A template pipeline is provided below. Each step of the pipeline has configuration options for experimenting with various methods. These are detailed in the documentation for each method. Notably, the `import_docs`, `get_cluster_topics`, `visualize_clustering`, and `evaluate` methods all include the option to save results to a file.

## Example Pipeline
### Import data
Import and pre-process documents from a text file containing a list of all documents.

```python
from medtop.core import *
path_to_file_list = 'data/corpus_file_list.txt'
data, doc_df = import_docs(path_to_file_list, save_results = False)
```


    ---------------------------------------------------------------------------

    NameError                                 Traceback (most recent call last)

    <ipython-input-3-94cd8af6b3a0> in <module>
    ----> 1 from medtop.core import *
          2 path_to_file_list = 'data/corpus_file_list.txt'
          3 data, doc_df = import_docs(path_to_file_list, save_results = False)
    

    ~\code\medtop\medtop\core.py in <module>
        136 def get_vectors(method:str, data:DataFrame, dictionary:gensim.corpora.dictionary.Dictionary = None,
        137                 tfidf:np.ndarray = None, dimensions:int = 2, umap_neighbors:int = 15,
    --> 138                 path_to_w2v_bin_file:str = None, doc_df:DataFrame = None):
        139     """
        140     Creates a word vector for each phrase in the dataframe.
    

    NameError: name 'gensim' is not defined


### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents.

```python
path_to_seed_topics_file_list = 'data/seed_topics_file_list.txt'
tfidf, dictionary = create_tfidf(path_to_seed_topics_file_list, doc_df)
data = get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = False)
data = get_vectors("tfidf", data, dictionary = dictionary, tfidf = tfidf)
```

**Questions about unrepresentative names:**   
  1) Need a better understanding of `include_input_in_tfidf`  
  2) Why is `token_averages` is the max of each row.

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics.

```python
data = assign_clusters(data, method = "hac")
cluster_df = get_cluster_topics(data, doc_df, save_results = False)
visualize_clustering(data, method = "umap", display_inline = False)
```

### Evaluate results

```python
gold_file = "data/gold_standard.txt"
results_df = evaluate(data, gold_file, save_results = False)
```
