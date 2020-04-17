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
      <th>id</th>
      <th>doc_id</th>
      <th>sent_id</th>
      <th>text</th>
      <th>tokens</th>
      <th>pos_tags</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>doc.0.sent.0</td>
      <td>0</td>
      <td>0</td>
      <td>I felt guilt because I was caught out lying ab...</td>
      <td>[guilt, wa, caught, lying, diary, engagement, ...</td>
      <td>[[guilt, NN], [was, VBD], [caught, VBN], [lyin...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>doc.0.sent.1</td>
      <td>0</td>
      <td>1</td>
      <td>I felt joy because I was going to South Africa...</td>
      <td>[joy, wa, going, south, africa, see, partner, ...</td>
      <td>[[joy, NN], [was, VBD], [going, VBG], [South, ...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>doc.0.sent.2</td>
      <td>0</td>
      <td>2</td>
      <td>I felt joy because I was going to see my favou...</td>
      <td>[joy, wa, going, see, favourite, music, artist...</td>
      <td>[[joy, NN], [was, VBD], [going, VBG], [see, VB...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>doc.0.sent.3</td>
      <td>0</td>
      <td>3</td>
      <td>I felt shame because I was not able to answer ...</td>
      <td>[shame, wa, able, answer, simple, question, exam]</td>
      <td>[[shame, NN], [was, VBD], [able, JJ], [answer,...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>doc.0.sent.4</td>
      <td>0</td>
      <td>4</td>
      <td>I felt joy because I was offered a promotion a...</td>
      <td>[joy, wa, offered, promotion, work, head, depa...</td>
      <td>[[joy, NN], [was, VBD], [offered, VBN], [promo...</td>
    </tr>
  </tbody>
</table>
</div>



### Transform data
Create word vectors from the most expressive phrase in each sentence of the imported documents.

NOTE: If `doc_df` is NOT passed to `create_tfidf`, you must set `include_input_in_tfidf=False` in `get_phrases`.

```python
tfidf, dictionary = create_tfidf(doc_df, 'test_data/seed_topics_file_list.txt')
data = get_phrases(data, dictionary.token2id, tfidf, include_input_in_tfidf = True)
data = get_vectors("tfidf", data, dictionary = dictionary, tfidf = tfidf)
```

    Removed 0 sentences without phrases.
    

### Cluster data
Cluster the sentences into groups expressing similar ideas or topics. If you aren't sure how many true clusters exist in the data, try running `assign_clusters` with the optional parameter `show_chart = True` to visual cluster quality with varying numbers of clusters. When using `method='hac'`, you can also use `show_dendrogram = True` see the cluster dendrogram.

```python
data = assign_clusters(data, method = "kmeans", k=4)
cluster_df = get_cluster_topics(data, doc_df, save_results = True)
visualize_clustering(data, method = "umap", show_chart = False)
cluster_df
```

    Results saved to output/TopicClusterResults.txt
    

    C:\Users\etfrench\Anaconda3\lib\site-packages\umap\spectral.py:229: UserWarning:
    
    Embedding a total of 2 separate connected components using meta-embedding (experimental)
    
    




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
      <td>[felt, joy, got, guilt, found, son, shame, for...</td>
      <td>37</td>
    </tr>
    <tr>
      <th>1</th>
      <td>1</td>
      <td>[felt, sadness, heard, died, dog, home, friend...</td>
      <td>14</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2</td>
      <td>[felt, guilt, joy, shame, sadness, friend, old...</td>
      <td>87</td>
    </tr>
    <tr>
      <th>3</th>
      <td>3</td>
      <td>[felt, guilt, lost, joy, sadness, managed, lie...</td>
      <td>16</td>
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
      <td>{doc.4.sent.17, doc.9.sent.6, doc.0.sent.0, do...</td>
      <td>2</td>
      <td>{doc.4.sent.15, doc.4.sent.8, doc.3.sent.12, d...</td>
      <td>31</td>
      <td>56</td>
      <td>37</td>
      <td>0.356</td>
      <td>0.456</td>
      <td>0.400</td>
    </tr>
    <tr>
      <th>1</th>
      <td>joy</td>
      <td>{doc.0.sent.19, doc.7.sent.2, doc.1.sent.19, d...</td>
      <td>0</td>
      <td>{doc.5.sent.4, doc.5.sent.5, doc.1.sent.10, do...</td>
      <td>23</td>
      <td>14</td>
      <td>40</td>
      <td>0.622</td>
      <td>0.365</td>
      <td>0.460</td>
    </tr>
    <tr>
      <th>0</th>
      <td>sadness</td>
      <td>{doc.1.sent.13, doc.4.sent.15, doc.1.sent.18, ...</td>
      <td>2</td>
      <td>{doc.4.sent.15, doc.4.sent.8, doc.3.sent.12, d...</td>
      <td>15</td>
      <td>72</td>
      <td>23</td>
      <td>0.172</td>
      <td>0.395</td>
      <td>0.240</td>
    </tr>
    <tr>
      <th>3</th>
      <td>shame</td>
      <td>{doc.8.sent.14, doc.4.sent.8, doc.4.sent.19, d...</td>
      <td>2</td>
      <td>{doc.4.sent.15, doc.4.sent.8, doc.3.sent.12, d...</td>
      <td>20</td>
      <td>67</td>
      <td>11</td>
      <td>0.230</td>
      <td>0.645</td>
      <td>0.339</td>
    </tr>
  </tbody>
</table>
</div>


