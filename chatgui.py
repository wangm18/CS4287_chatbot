from json import dumps
from json import loads
import random
import couchdb
from kafka import KafkaProducer  # producer of events
from kafka import KafkaConsumer  # consumer of events

couch = couchdb.Server('http://admin:password@129.114.26.34:5984/')
database = couch["chatbot-intents"]
intents = database['chatbot_intents']


producer = KafkaProducer(bootstrap_servers=['129.114.26.34:9092'],
                         value_serializer=lambda x: 
                         dumps(x).encode('utf-8'))

consumer = KafkaConsumer (bootstrap_servers="129.114.26.34:9092", value_deserializer=lambda x: loads(x.decode('utf-8')), auto_offset_reset='earliest', enable_auto_commit=False, consumer_timeout_ms=5000)


#Creating GUI with tkinter
import tkinter
from tkinter import *


def send():
    msg = EntryBox.get("1.0",'end-1c').strip()
    EntryBox.delete("0.0",END)

    if msg != '':
        ChatLog.config(state=NORMAL)
        ChatLog.insert(END, "You: " + msg + '\n\n')
        ChatLog.config(foreground="#442265", font=("Verdana", 12 ))

        #res = chatbot_response(msg)
        
        consumer.subscribe (topics=["chatbot_responses"])        
        producer.send('chatbot', value=msg)
        producer.flush()
        received_response = False
        res = ""
        while received_response == False:
            for msg in consumer:
                res = str(msg.value)
                received_response = True
                

        ChatLog.insert(END, "Bot: " + res + '\n\n')

        ChatLog.config(state=DISABLED)
        ChatLog.yview(END)


base = Tk()
base.title("Hello")
base.geometry("400x500")
base.resizable(width=FALSE, height=FALSE)

#Create Chat window
ChatLog = Text(base, bd=0, bg="white", height="8", width="50", font="Arial",)

ChatLog.config(state=DISABLED)

#Bind scrollbar to Chat window
scrollbar = Scrollbar(base, command=ChatLog.yview, cursor="heart")
ChatLog['yscrollcommand'] = scrollbar.set

#Create Button to send message
SendButton = Button(base, font=("Verdana",12,'bold'), text="Send", width="12", height=5,
                    bd=0, bg="#32de97", activebackground="#3c9d9b",fg='#ffffff',
                    command= send )

#Create the box to enter message
EntryBox = Text(base, bd=0, bg="white",width="29", height="5", font="Arial")
#EntryBox.bind("<Return>", send)


#Place all components on the screen
scrollbar.place(x=376,y=6, height=386)
ChatLog.place(x=6,y=6, height=386, width=370)
EntryBox.place(x=128, y=401, height=90, width=265)
SendButton.place(x=6, y=401, height=90)

base.mainloop()
