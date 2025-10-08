from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import create_react_agent
import os
from urllib.parse import quote_plus


import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

OPENAI_KEY_ENV = "KEY_FOR_OPENAI_LEARNING_LANGCHAIN"

# ---------- Helper: create agent dynamically ----------
def create_sql_agent(db_name: str):
    # Encode password safely for connection string
    encoded_pwd = quote_plus(DB_CONFIG["password"])
    """Creates a LangGraph SQL agent for a given Postgres database."""
    db_uri = f"postgresql+psycopg2://{DB_CONFIG['user']}:{encoded_pwd}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
    db = SQLDatabase.from_uri(db_uri)

    os.environ["OPENAI_API_KEY"] = os.getenv(OPENAI_KEY_ENV)
    llm = init_chat_model("openai:gpt-5-nano", temperature=0)

    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    system_prompt = f"""
    You are an agent designed to interact with a SQL database.
    Given an input question, create a syntactically correct {db.dialect} query to run,
    then look at the results of the query and return the answer. Unless the user
    specifies a specific number of examples they wish to obtain, always limit your
    query to at most 5 results.

    You can order the results by a relevant column to return the most interesting
    examples in the database. Never query for all the columns from a specific table,
    only ask for the relevant columns given the question.

    You MUST double check your query before executing it. If you get an error while
    executing a query, rewrite the query and try again.

    DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.

    To start you should ALWAYS look at the tables in the database to see what you
    can query. Do NOT skip this step.

    Then you should query the schema of the most relevant tables.
    """

    agent = create_react_agent(llm, tools, prompt=system_prompt)
    return agent
