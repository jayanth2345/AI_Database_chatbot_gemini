import os
import sys

# Add the parent directory (project root) to Python's module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from utils import getValuefromDB,get_sql_local, get_NLP_response_local,retry_sql_local

# getValuefromDB,get_sql_local, get_NLP_response_local,retry_sql_local
load_dotenv()

global history
history = []
def addtohistory(role,message):
    global history
    history.append(f" role : {role} , message : {message} ")

print(" Welcome, please chat with your database here..")    

async def main():
    try:
        while(True):
            question = input("user : ")
            addtohistory('user', question)
            sql_command = await get_sql_local(question,history)
            
            answer = getValuefromDB(sql_command)
            if answer == "wrong_sql":
                new_sql = await retry_sql_local(question, sql_command, history)
                answer = getValuefromDB(new_sql)
            
            reply = await get_NLP_response_local(question,answer,history)
            print(f"Model : {reply}")
            addtohistory('model',reply)
    except KeyboardInterrupt:        
        print(f"\n\n Thank you for using the chatbot")
    except Exception as e:
        print(f" There is an issue : {e}")


asyncio.run(main())