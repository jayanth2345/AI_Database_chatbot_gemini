# Chatbot with LLM-Powered Database Interaction

This project is a chatbot that uses the power of **LLMs** (like **Gemini API** or a **local model**) to interact with a **PostgreSQL** database in natural language.  
It converts user questions into SQL queries, retrieves data using **psycopg2**, and then responds back in **natural language**.

---

## 🧩 Features

- Converts user questions into SQL queries using **Gemini API** or a **local LLM model**
- Executes SQL queries on a **PostgreSQL** database
- Returns answers in **natural language** based on query results
- Handles general conversation and chat history when no database query is needed
- Responds gracefully if no records are found

---

## 🔄 Project Flow

1. **User Input** – User asks a question in plain English  
2. **SQL Generation** – LLM (Gemini or local model) converts the question into an SQL query  
3. **Database Execution** – The generated SQL is executed using **psycopg2**  
4. **Response Generation** – The chatbot summarizes and replies with a natural language answer based on query results  

---

## ⚙️ Requirements

- `psycopg2-binary`  
- `google-genai`  
- `vllm`  
- `aiohttp`  
- `bitsandbytes>=0.46.1`  
- `huggingface-cli`  
- Access to **Gemini API** or a **local LLM model**

---

## 🧰 Setup

1. **Clone this repository**   
   git clone <your-repo-url>
   cd <your-repo-folder>
2. **Install dependencies**
    pip install -r requirements.txt

3. **Set up your PostgreSQL database**

    Use the provided bookstore_schema.sql file to create the database schema.

4. **Configure your credentials**

    Add your database credentials and Gemini/local model configuration
    in the config file or set them as environment variables. Follow the sample_env file format

