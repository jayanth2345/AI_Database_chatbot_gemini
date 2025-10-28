
import os
import sys
# Add the parent directory (project root) to Python's module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from utils import getValuefromDB,get_sql_gemini,get_NLP_response_gemini
from google import genai    
load_dotenv()
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))
global history
history = []
def addtohistory(role,message):
    global history
    history.append(f" role : {role} , message : {message} ")

print(" Welcome, please chat with your database here..")    
try:
    while(True):
        question = input("user : ")
        addtohistory('user', question)
        sql_command = get_sql_gemini(client,question,history)
        answer = getValuefromDB(sql_command)
        reply = get_NLP_response_gemini(client,question,answer,history)
        print(f"Model : {reply}")
        addtohistory('model',reply)
except KeyboardInterrupt:        
    print(f"\n\n Thank you for using the chatbot")
except Exception as e:
    print(f" There is an issue : {e}")



