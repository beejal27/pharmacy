from fastapi import FastAPI, Query, HTTPException
from sql_agent import create_sql_agent
from typing import Generator
from pydantic import BaseModel
from typing import Generator
import os, time, json

# ---------- Request schema ----------
class QueryRequest(BaseModel):
    question: str

# ---------- FastAPI setup ----------
app = FastAPI(title="LangGraph SQL Agent API")

# ---------- Hard limit setup ----------
USAGE_LOG = "/tmp/openai_usage.json"
DAILY_LIMIT = 1  # max requests per day

def check_limit():
    today = time.strftime("%Y-%m-%d")
    if os.path.exists(USAGE_LOG):
        with open(USAGE_LOG) as f:
            data = json.load(f)
    else:
        data = {}

    count = data.get(today, 0)
    if count >= DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="Daily limit reached.")
    else:
        data[today] = count + 1
        with open(USAGE_LOG, "w") as f:
            json.dump(data, f)

# ---------- Helper: stream responses ----------
def stream_agent_response(agent, question: str) -> Generator[str, None, None]:
    for step in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        yield step["messages"][-1].content


# ---------- API endpoint ----------
@app.post("/ask")
def ask_sql_agent(
    payload: QueryRequest,
    db_name: str = Query(..., description="Name of the Postgres database"),
):
    """
    Ask the SQL agent a question about the specified database.
    Example: POST /ask?db_name=pharmacy
    Body: {"question": "Show top 5 medicines by revenue"}
    """
    check_limit()
    agent = create_sql_agent(db_name)
    final_answer = None
    for chunk in stream_agent_response(agent, payload.question):
        final_answer = chunk
    return {"database": db_name, "question": payload.question, "answer": final_answer}