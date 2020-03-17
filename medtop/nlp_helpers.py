# AUTOGENERATED! DO NOT EDIT! File to edit: nlp_helpers.ipynb (unless otherwise specified).

__all__ = ['get_term_averages', 'get_term_max', 'get_top_phrases', 'get_vec', 'get_phrase_vec_tfidf',
           'get_phrase_vec_w2v', 'average_sent_size', 'w2v_from_corpus', 'w2v_pretrained', 'merge_doc_lists',
           'create_tfidf']

# Cell
def get_term_averages(tdm):
    #print(len(tdm))
    #print(len(tdm[0]))

    avg_vec = numpy.zeros(len(tdm))
    for i in range(0,len(tdm)):
        for j in range(0,len(tdm[0])):
            avg_vec[i] = avg_vec[i] + tdm[i,j]
        avg_vec[i] = avg_vec[i]/len(tdm[0])

    return(avg_vec)

# Cell
def get_term_max(tdm):
    #print(len(tdm))
    #print(len(tdm[0]))

    avg_vec = numpy.zeros(len(tdm))
    for i in range(0,len(tdm)):
        avg_vec[i] = max(tdm[i])

    return(avg_vec)

# Cell
def get_top_phrases(text_id, text, feature_names, tdm, size, include_input_in_tfidf):
    """
    Gets top phrase for each sentence and returns them as a list of lists\n
    One entry for each sentence.  If there are no phrases then a "none" is returned for that sentences value.
    """
    if not include_input_in_tfidf:
        token_averages = get_term_max(tdm)


    top_sent_phrases = []
    #print("Processing Doc: " + str(text_id))
    for sentence in nltk.sent_tokenize(text):

        sent_tokens, sent_tokens_pos, sent_tokens_loc, my_tokens, my_pos_tags, my_loc, d1, d2, d3, d4 = tokenize_and_stem(sentence)

        sent_token_scores = []
        phrase_scores = []
        for p in range(size,len(my_tokens)+1):
            phrase = my_tokens[p-size:p]
            phrase_pos = my_pos_tags[p-size:p]
            phrase_loc = my_loc[p-size:p]
            weight = 1 + abs(TextBlob(" ".join(phrase)).sentiment.polarity)
            score = 0
            #print("Processing Phrase: " + str(phrase))

            ## get tokens and associated POS tags that are in the TF-IDF matrix
            avaliable_tokens = []
            avaliable_pos = []
            avaliable_loc = []

            for n in range(0, len(phrase)):
                if phrase[n] in list(feature_names.keys()):
                    avaliable_tokens.append(phrase[n])
                    avaliable_pos.append(phrase_pos[n])
                    avaliable_loc.append(phrase_loc[n])
                #else:
                    #print("Token not in TF-IDF: " + str(phrase[n]))

            #new_vec = dictionary.doc2bow(phrase[1]) #convert phrase to a vector of ids and counts
            #vec_ids = [x[0] for x in new_vec]  #get word IDs in dictionary

            for t in range(0, len(avaliable_tokens)):

                if avaliable_pos[t][1] in ["JJ","JJR", "JJS", "RB", "RBR", "RBS"]:
                    #print("Found adverb or adjective")
                    index = feature_names[avaliable_tokens[t]]
                    #print(str(tdm[index, text_id]))
                    if include_input_in_tfidf:
                        #print("executing1")
                        score += tdm[index, text_id]*3
                    else:
                        score += token_averages[index]*3
                else:
                    #print("not JJ or RB")
                    index = feature_names[avaliable_tokens[t]]
                    #print(str(tdm[index, text_id]))
                    if include_input_in_tfidf:
                        #print("executing2")
                        score += tdm[index, text_id]
                    else:
                        score += token_averages[index]

            phrase_scores.append((score*weight, phrase, phrase_loc))  #*weight, phrase))
            #print("Phrase Score: " + str(score))

        ## sort phrase scores for this sentence and choose the highest to represent sentence
        phrase_scores.sort(key=lambda sent: sent[0], reverse=True)
        #if len(phrase_scores) > 0:
            #print(sentence)
            #print(phrase_scores[0])
        top_sent_phrases.append(phrase_scores[0]) if len(phrase_scores) > 0 else top_sent_phrases.append("none")


    return top_sent_phrases

# Cell
def get_vec(term, dictionary, u):
    p_vec = numpy.zeros(len(u[0]))
    new_vec = dictionary.doc2bow([term]) #convert phrase to a vector of ids and counts
    vec_ids = [x[0] for x in new_vec]  #get word IDs in dictionary
    for i in vec_ids:
        # get the SVD vector for this word ID
        p_vec = p_vec + u[i]

    return p_vec

# Cell
def get_phrase_vec_tfidf(doc_top_phrases, dictionary, term_matrix):
    doc_phrase_vecs = []
    for doc in doc_top_phrases:
        phrases_vec = []
        for phrase in doc:
            p_vec = numpy.zeros(len(term_matrix[0]))

            if phrase is not "none":
                new_vec = dictionary.doc2bow(phrase[1]) #convert phrase to a vector of ids and counts
                vec_ids = [x[0] for x in new_vec]  #get word IDs in dictionary
                for i in vec_ids:
                    p_vec = p_vec + term_matrix[i]

            phrases_vec.append(p_vec)#/len(phrase))
        doc_phrase_vecs.append(phrases_vec)
    return(doc_phrase_vecs)

# Cell
def get_phrase_vec_w2v(doc_top_phrases, model2):
    doc_phrase_vecs = []

    for doc in doc_top_phrases:
        phrases_vec = []
        for phrase in doc:
            p_vec = 0

            if phrase is not "none":
                for tok in phrase[1]:
                    if tok in model2.wv.vocab:
                        p_vec = p_vec + model2.wv[tok]
                    else:
                        print(tok + ": not in Corpus")

            phrases_vec.append(p_vec)#/len(phrase))
        doc_phrase_vecs.append(phrases_vec)
    return doc_phrase_vecs

# Cell
def average_sent_size(my_docs):
    doc_sum = 0

    for doc in my_docs:
        sent_sum = 0
        #print("Doc Length" + str(len(doc)))
        for sent in doc:
            sent_sum = sent_sum + len(sent)
            #print("Sent Length" + str(len(sent)))
            #print("Sentence:" + str(sent))

        if len(doc) > 0:
            doc_sum = doc_sum + sent_sum/len(doc)

    total_average = doc_sum/len(my_docs)
    return(total_average)

# Cell
def w2v_from_corpus(file_content, my_docs):
    ##extract all sentences from each doc into one large sentence vector
    ## so each document is just a bag of words
    large_sent_vec = []
    for doc in file_content:
        flattened_list = [y for x in tokenize_and_stem(doc)[6] for y in x]
        large_sent_vec.append(flattened_list)

    sent_avg_size = average_sent_size(my_docs)

    model2 = gensim.models.Word2Vec(sg=1, window = 6, max_vocab_size = None, min_count=1, size = 10, iter=500)
    model2.build_vocab(large_sent_vec)
    model2.train(large_sent_vec, total_examples=model2.corpus_count, epochs=model2.iter)
    return(model2)

# Cell
def w2v_pretrained(bin_file):
    return gensim.models.KeyedVectors.load_word2vec_format(bin_file, binary=True)

# Cell
def merge_doc_lists(doc1, doc2):
    file_list1 = open(doc1).read().strip().split('\n')
    file_list2 = open(doc2).read().strip().split('\n')

    return(file_list1 + file_list2)

# Cell
def create_tfidf(documents1, documents2="none"):
    "Input: the path to and name of a files containing the list of documents to use for the tf-idf matrix creation."
    ### import documents
    if documents2 == "none":
        file_list = open(documents1).read().strip().split('\n')
    else:
        file_list = merge_doc_lists(documents1, documents2)

    file_content = []
    for file_path in file_list:
        if file_path is not '':
            file = open(file_path, "r")
            text = file.read()
            file_content.append(text)

    ### Pre-processing corpus
    my_docs = []

    for doc in file_content:
        split_sent, split_sent_pos, split_sent_loc, tokens, pos, loc, full_sent, full_pos, full_loc, raw_sent = tokenize_and_stem(doc)
        my_docs.append(split_sent)

    ### Get the TF-IDF matrix
    bog_docs = []
    for doc in my_docs:
        bog = [y for x in doc for y in x]
        bog_docs.append(bog)

    dictionary = corpora.Dictionary(bog_docs)
    corpus = [dictionary.doc2bow(text) for text in bog_docs]
    tfidf = models.TfidfModel(corpus)
    corpus_tfidf=tfidf[corpus]
    num_terms = len(corpus_tfidf.obj.idfs)
    tfidf_dense = matutils.corpus2dense(corpus_tfidf, num_terms)

    return(tfidf_dense, dictionary)