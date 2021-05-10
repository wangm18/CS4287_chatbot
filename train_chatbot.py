import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.optimizers import SGD
import random
import couchdb

nltk.download('punkt')
nltk.download('wordnet')
lemmatizer = WordNetLemmatizer()

couch = couchdb.Server('http://admin:password@129.114.26.34:5984/')
database = couch["chatbot-intents"]
intents = database['chatbot_intents']

words=[] #contains all known unique lemmatized words
classes = [] #contains all known intents
documents = [] #contains "docs", which are a two-part data structure of 1. list of tokenized words, and 2. their intent
ignore_words = ['?', '!']

for intent in intents['intents']:
    for pattern in intent['patterns']:
        w = nltk.word_tokenize(pattern)
        words.extend(w)
        documents.append((w, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))
classes = sorted(list(set(classes)))

pickle.dump(words,open('words.pkl','wb'))
pickle.dump(classes,open('classes.pkl','wb'))

training = [] #master data structure that's a list of pairs. The pair consists of 1. a list of 1's and 0's the length of the total number of known lemmatized words and 2. a list of 1's and 0's the length of the number of intents. These pairs map the tokenized patterns to their respective intents via index-based identification, based on the original "words" and "classes" lists.

output_empty = [0] * len(classes)
for doc in documents:
    bag = []
    pattern_words = doc[0]
    pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1

    training.append([bag, output_row])
    
# shuffle our features and turn into numpy.array
random.shuffle(training)
training = numpy.array(training)

# create train and test lists. X - patterns, Y - intents
train_x = list(training[:,0])
train_y = list(training[:,1])
print("Training data created")

# Create model - 3 layers. First layer 128 neurons, second layer 64 neurons and 3rd output layer contains number of neurons
# equal to number of intents to predict output intent with softmax
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

#fitting and saving the model
hist = model.fit(np.array(train_x), np.array(train_y), epochs=1000, batch_size=5, verbose=1)
model.save('chatbot_model.h5', hist)

print("model created")
