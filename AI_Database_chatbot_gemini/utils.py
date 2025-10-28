import json
import re
import os
import aiohttp
from dotenv import load_dotenv
from google import genai
import psycopg2
load_dotenv()


model = "/home/ajai/Music/AI/AI_Database_chatbot_gemini/models/llama-3.2-1b-instruct-fp16/"
url = "http://localhost:8000/v1/chat/completions"  # vLLM server endpoint

headers = {
        "Content-Type": "application/json",
    }

gemini_prompt = """
        You ae a Text-to-SQL assistant. Given a user's natural language question and the schema below, generate a valid and executable PostgreSQL query that answers the question. 

        ## General Instructions:
        - Always use **only the tables and columns** provided in the schema.
        - Be **concise and correct**, with proper SQL syntax.
        - Do **not add any assumptions** beyond the schema.
        - Use **JOINs, GROUP BY, ORDER BY, etc.** where needed.
        - Return **only the SQL query** and nothing else.
        - Refer to the schema below before answering.
        - Use the chat history attached to get the context of the current question , if it depends on any of previous chats.
        - If the requested question can't be converted to a valid sql with given schema - return - 'Invalid'

        ---

        ## Few-Shot Examples:

        ### Q1: List all books ordered by Alice Smith.
        output : ```sql
        SELECT b.title
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN books b ON oi.book_id = b.book_id
        WHERE c.name = 'Alice Smith';
        ```


        ###Q2 : Find total amount spent by each customer.
        output : ``` sql 
        SELECT c.name, SUM(b.price * oi.quantity) AS total_spent
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN books b ON oi.book_id = b.book_id
        GROUP BY c.name;
        ```           
    """

database_schema = """
        Database Schema:
        Table: customers
            customer_id (PK): integer
            name: text
            email: text

        Table: books
            book_id (PK): integer
            title: text
            author: text
            price: numeric(6,2)

        Table: orders
            order_id (PK): integer
            customer_id (FK → customers.customer_id): integer
            order_date: date

        Table: order_items
            order_item_id (PK): integer
            order_id (FK → orders.order_id): integer
            book_id (FK → books.book_id): integer
            quantity: integer
            """


local_model_prompt = """
  You are an expert Text-to-SQL translator for PostgreSQL. 
Your job is to convert a natural language question into exactly one valid SQL query.

Follow these rules strictly:
1. Use only the columns and tables provided in the schema.
2. Do not invent new fields, values, or tables.
3. If the question cannot be answered with the given schema, output exactly:
   Invalid
4. Output format:
   ```sql
   <SQL_QUERY>
or
Invalid

Database Schema:

customers(customer_id PK, name, email)

books(book_id PK, title, author, price)

orders(order_id PK, customer_id FK→customers.customer_id, order_date)

order_items(order_item_id PK, order_id FK→orders.order_id, book_id FK→books.book_id, quantity)

Conversation context:
{history}

Question:
{question}
"""

def get_sql_gemini(client : genai.Client, question, chat_history):
    response = client.models.generate_content(
        model = "gemini-2.5-flash",
        contents = f"context : {gemini_prompt} ,  Question : {question} , chat_history : {chat_history}"
    )
    query = re.sub(r"^```[ \t]*sql[ \t]*\n?","", response.text,flags=re.IGNORECASE)
    query = re.sub(r"\n?```$","", query)
    return query


def get_NLP_response_gemini(client: genai.Client, question, response, chat_history):
    prompt = f"""
        You are part of a system that converts SQL query results into natural language responses within an ongoing chat conversation.

        ### Task
        Given the following:
        - **User Question/Message:** {question}
        - **SQL Response (from the database):** {response}
        - **Conversation Context / Chat History:** {chat_history}

        Your job is to produce a natural language reply that is:
        1. Clear, helpful, and easy to understand.
        2. Contextually appropriate — take the conversation history into account to maintain a coherent dialogue.
        3. Sensitive to the **intent of the user’s message** — some messages may be follow-ups, acknowledgments, or casual remarks that do not require factual data from the SQL response.

        ### Guidelines
        - If the SQL response contains relevant data, summarize it clearly and naturally.
        - If the SQL response is empty, invalid, or doesn’t match the user’s intent:
            - Determine if the user message is a general remark or conversational acknowledgment (e.g., “oh nice”, “good to know”, “thanks”) — in this case, respond politely without referencing the SQL or pointing out an error.
            - If the user is clearly asking a follow-up **query** but the response is empty or mismatched, indicate that there may be no data or a misunderstanding, in a graceful and helpful tone.
        - **Never repeat the SQL query or raw response.** Focus solely on providing a smooth natural language reply.
        - Keep responses polite, relevant, and conversational.

        ### Output
        Respond only with the natural language answer.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


def getValuefromDB(command):
    try : 
        if "invalid" in command.lower():
            return 'Invalid'
        conn = psycopg2.connect(    
                                    database = os.environ.get('DB_NAME', 'test'),
                                    user = os.environ.get('DB_USER', 'postgres'), 
                                    password = os.environ.get('DB_PASS', 'pass'), 
                                    host = os.environ.get('DB_HOST', 'localhost'),
                                    port = os.environ.get('DB_PORT', 5432)
                                )
        cur = conn.cursor()
        cur.execute(command)
        res = cur.fetchall()        
        cur.close()
        conn.close()
        return res
    except Exception as e :        
        return 'wrong_sql'
    

async def get_sql_local(question,history:list):
    last_history = []
    if len(history) >= 2 :
        last_history = history[-2:]
    if len(history) == 1:
        last_history = history[-1]    
    formatted_prompt = local_model_prompt.format(
        question=question,
        history=last_history
    )
    payload = {
        "model": f"{model}",
        "messages": [
            {"role": "system", "content": f"{formatted_prompt}"},
            {"role": "user", "content": f"Generate the SQL for the above question."}
        ],
        "max_tokens": 150,
        "temperature": 0.2,

    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            raw_output = data["choices"][0]["message"]["content"]

            # Extract only the SQL
            match = re.search(r"```sql\s*(.*?)```", raw_output, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip().rstrip(';') + ';'
            else:
                sql = "Invalid"
            return sql
        

async def get_NLP_response_local(question, response, chat_history):
    formatted_response = summarize_sql_result(response)
    prompt = f"""
        You are a database assistant. Give a short natural reply using the SQL result.

        User question: "{question}"
        SQL result summary: {formatted_response}
        Chat history: {chat_history}

        Rules:
        - Answer in one short sentence.
        - If the result is a list of people, mention their names naturally.
        - If the result is numeric, say the number.
        - If it's empty, say "No records found."
        - Never mention SQL or databases.
    """
    payload = {
        "model": f"{model}",
        "messages": [
            {"role": "system", "content": f"{prompt}"},            
        ],
        "max_tokens": 60,
        "temperature": 0.1,

    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers,json=payload) as resp:
            data = await resp.json()
            raw_output = data["choices"][0]["message"]["content"].strip()            
            return raw_output


def summarize_sql_result(sql_result):
    if not sql_result:
        return "No records"
    
    # Handle list of tuples like [(1, 'Alice', 'alice@x.com'), ...]
    if isinstance(sql_result, list) and isinstance(sql_result[0], tuple):
        # Convert up to 3 rows for preview        
        return "; ".join([", ".join(map(str, row)) for row in sql_result])    
    return str(sql_result)


async def retry_sql_local(question, previous_sql : str, chat_history):
    if "invalid" in  previous_sql.lower():
        return previous_sql
    
    correct_sql_prompt = f"""
        You are an expert Text-to-SQL translator for PostgreSQL.

        The previous SQL query generated for the user's question was incorrect.
        Your task is to generate a **new corrected SQL query** using the database schema and conversation context below.

        Rules:
        1. Use only the tables and columns listed in the schema.
        2. Do not invent new fields, tables, or assumptions.
        3. Ensure the SQL syntax is valid and executable.
        4. If no valid SQL can be created, respond exactly with:
        Invalid
        5. Output format (strictly one of the two):
        ```sql
        <correct SQL query>
        or
        Invalid

        Database Schema:
        customers(customer_id PK, name, email)
        books(book_id PK, title, author, price)
        orders(order_id PK, customer_id FK→customers.customer_id, order_date)
        order_items(order_item_id PK, order_id FK→orders.order_id, book_id FK→books.book_id, quantity)

        Conversation history:
        {chat_history}

        User question:
        {question}

        Incorrect SQL to fix:
        {previous_sql}
    """
    payload = {
        "model": f"{model}",
        "messages": [
            {"role": "system", "content": f"{correct_sql_prompt} "},            
        ],
        "max_tokens": 150,
        "temperature": 0.2,

    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()            
            raw_output = data["choices"][0]["message"]["content"]

            # Extract only the SQL
            match = re.search(r"```sql\s*(.*?)```", raw_output, re.DOTALL | re.IGNORECASE)
            if match:
                sql = match.group(1).strip().rstrip(';') + ';'
            else:
                sql = "Invalid"            
            return sql
