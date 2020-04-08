![CI](https://github.com/cctrbic/medtop/workflows/CI/badge.svg) 

Documentation is available at https://cctrbic.github.io/medtop/.

# MedTop
> Extracting topics from reflective medical writings.


## Requirements
`pip install medtop` *Not actually available via pip yet

`python -m nltk.downloader all`

## How to use

A template pipeline is provided below using a test dataset. You can read more about the test_data dataset [here](https://github.com/cctrbic/medtop/blob/master/test_data/README.md)

Each step of the pipeline has configuration options for experimenting with various methods. These are detailed in the documentation for each method. Notably, the `import_docs`, `get_cluster_topics`, `visualize_clustering`, and `evaluate` methods all include the option to save results to a file.

## Example Pipeline
### Import data
Import and pre-process documents from a text file containing a list of all documents.

```python
from medtop.core import *
data, doc_df = import_docs('test_data/corpus_file_list.txt', save_results = True)
```

    Results saved to output/DocumentSentenceList.txt
    

### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents.

```python
tfidf, dictionary = create_tfidf('test_data/seed_topics_file_list.txt', doc_df)
data = get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = True)
data = get_vectors("tfidf", data, dictionary = dictionary, tfidf = tfidf)
```

    Removed 43 sentences without phrases.
    

**Questions about unrepresentative names:**   
  1) Need a better understanding of `include_input_in_tfidf`  
  2) Why is `token_averages` is the max of each row.

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics.

```python
data = assign_clusters(data, method = "kmeans", k=4)
cluster_df = get_cluster_topics(data, doc_df, save_results = True)
visualize_clustering(data, method = "umap", show_chart = False)
cluster_df
```

    Results saved to output/TopicClusterResults.txt
    




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>cluster</th>
      <th>topics</th>
      <th>sent_count</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>0</td>
      <td>[felt, guilt, lost, lied, joy, friend, sadness...</td>
      <td>14</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>[felt, guilt, joy, shame, christmas, friend, n...</td>
      <td>75</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2</td>
      <td>[felt, joy, got, found, guilt, shame, son, gav...</td>
      <td>25</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3</td>
      <td>[felt, sadness, died, heard, friend, dog, joy,...</td>
      <td>40</td>
    </tr>
  </tbody>
</table>
</div>



### Evaluate results

```python
gold_file = "test_data/gold.txt"
evaluate(data, gold_file="test_data/gold.txt", save_results = False)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>label</th>
      <th>gold_examples</th>
      <th>closest_cluster</th>
      <th>closest_cluster_members</th>
      <th>tp</th>
      <th>fp</th>
      <th>fn</th>
      <th>precision</th>
      <th>recall</th>
      <th>f1</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>2</th>
      <td>guilt</td>
      <td>{doc.5.sent.9, doc.4.sent.1, doc.9.sent.5, doc...</td>
      <td>1</td>
      <td>{doc.4.sent.1, doc.6.sent.9, doc.9.sent.17, do...</td>
      <td>32</td>
      <td>43</td>
      <td>36</td>
      <td>0.427</td>
      <td>0.471</td>
      <td>0.448</td>
    </tr>
    <tr>
      <th>0</th>
      <td>joy</td>
      <td>{doc.2.sent.9, doc.5.sent.3, doc.6.sent.12, do...</td>
      <td>1</td>
      <td>{doc.4.sent.1, doc.6.sent.9, doc.9.sent.17, do...</td>
      <td>25</td>
      <td>50</td>
      <td>38</td>
      <td>0.333</td>
      <td>0.397</td>
      <td>0.362</td>
    </tr>
    <tr>
      <th>3</th>
      <td>sadness</td>
      <td>{doc.3.sent.2, doc.7.sent.15, doc.0.sent.17, d...</td>
      <td>3</td>
      <td>{doc.3.sent.2, doc.7.sent.15, doc.0.sent.17, d...</td>
      <td>27</td>
      <td>13</td>
      <td>11</td>
      <td>0.675</td>
      <td>0.711</td>
      <td>0.693</td>
    </tr>
    <tr>
      <th>1</th>
      <td>shame</td>
      <td>{doc.6.sent.9, doc.9.sent.17, doc.3.sent.15, d...</td>
      <td>1</td>
      <td>{doc.4.sent.1, doc.6.sent.9, doc.9.sent.17, do...</td>
      <td>18</td>
      <td>57</td>
      <td>13</td>
      <td>0.240</td>
      <td>0.581</td>
      <td>0.340</td>
    </tr>
  </tbody>
</table>
</div>


