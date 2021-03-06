import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import numpy
from keras.models import load_model
import json
from json import loads
from json import dumps
import random
import couchdb
from kafka import KafkaConsumer  # consumer of events
from kafka import KafkaProducer  # producer of events

couch = couchdb.Server('http://admin:password@129.114.26.34:5984/')
database = couch["chatbot-intents"]
intents = database['chatbot_intents']
consumer = KafkaConsumer (bootstrap_servers="129.114.26.34:9092",
value_deserializer=lambda x: loads(x.decode('utf-8')))
consumer.subscribe (topics=["chatbot"])    
producer = KafkaProducer(bootstrap_servers=['129.114.26.34:9092'],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))

words = pickle.load(open('words.pkl','rb'))
classes = pickle.load(open('classes.pkl','rb'))

lemmatizer = WordNetLemmatizer()
model = load_model('chatbot_model.h5')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(numpy.array(bag))

def predict_class(sentence, model):
    # filter out predictions below a threshold
    print("SENTENCE@@@@@@@@@@:", sentence)
    p = bow(sentence, words,show_details=False)
    res = model.predict(numpy.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    print(return_list)
    return return_list

def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if(i['tag']== tag):
            result = random.choice(i['responses'])
            break
    return result

def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = getResponse(ints, intents)
    return res

for msg in consumer:
    print(msg)
    res = chatbot_response(str(msg.value))
    producer.send('chatbot_responses', value=res)
    producer.flush()
