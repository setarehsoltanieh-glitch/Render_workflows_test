from render_sdk import Workflows
from pydantic import BaseModel
from models import Plan, PlanStep
from openai import AsyncOpenAI
from dotenv import load_dotenv
import json

load_dotenv()
app = Workflows()

PLANNER_PROMPT = """\
You are a movie recommendation planner. Given a user's request, produce a complete plan as an ordered list of tool calls.

Available tools:
- search_reddit(query: str)        Search Reddit for community recommendations.
- search_web(query: str)           Search the web for critic reviews and movie details.
- generate_report(raw_data: str)   Synthesize raw research into a clean report.
- write_file(args_json: str)       Save the report to disk. Pass "path|content" (pipe-separated).

Rules:
- Always call search_reddit and search_web before generate_report.
- The params for generate_report should be the literal string "{{search_reddit_result}} {{search_web_result}}" — the workflow will substitute real results at runtime.
- The params for write_file should be "recommendations.txt|{{generate_report_result}}" — the workflow will substitute the real report at runtime.

Respond ONLY with valid JSON:
{
  "steps": [
    {"tool": "<tool name>", "params": "<argument>"},
    ...
  ]
}
"""

@app.task()
async def search_web(query: str) -> str:
    """LLM agent that acts as a web search engine for movie information."""
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a web search agent specializing in movies. "
                    "Given a search query, return realistic search results including "
                    "critic reviews, Rotten Tomatoes/IMDb scores, plot summaries, and release info. "
                    "Format your response as a concise list of 3-5 results, each with a title and key details."
                ),
            },
            {"role": "user", "content": f"Search query: {query}"},
        ],
    )
    return response.choices[0].message.content


@app.task()
async def search_reddit(query: str) -> str:
    """LLM agent that acts as a Reddit search engine for community movie opinions."""
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Reddit search agent. Given a search query about movies, "
                    "return realistic Reddit-style posts and comments from subreddits like "
                    "r/movies, r/MovieSuggestions, and r/netflix. "
                    "Include post titles, upvote counts, and representative community opinions. "
                    "Format as 3-5 posts with brief comment highlights."
                ),
            },
            {"role": "user", "content": f"Search query: {query}"},
        ],
    )
    return response.choices[0].message.content


@app.task()
async def generate_report(raw_data: str) -> str:
    """LLM agent that synthesizes raw research into a clean movie recommendation report."""
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional movie critic and writer. "
                    "Given raw research data from web searches and Reddit, produce a clean, polished "
                    "movie recommendation report. Structure it as:\n"
                    "- A title and short introduction\n"
                    "- For each movie: title, year, genre, plot summary, critic sentiment, community sentiment, and why to watch it\n"
                    "- A closing recommendation summary\n"
                    "Write in clean prose. No raw JSON, no tool artifacts, no repetition."
                ),
            },
            {"role": "user", "content": f"Raw research data:\n\n{raw_data}"},
        ],
    )
    return response.choices[0].message.content


@app.task()
async def write_file(args_json: str) -> str:
    """Write content to a local file. Expects: 'path|content' (pipe-separated)."""
    try:
        path, content = args_json.split("|", 1)
        with open(path.strip(), "w") as f:
            f.write(content)
        return f"[write_file] Wrote {len(content)} chars to {path.strip()}"
    except Exception as e:
        return f"[write_file] Error: {e}"


@app.task()
async def create_plan(goal: str) -> Plan:
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": f"User request: {goal}"},
        ],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    return Plan(steps=[PlanStep(**s) for s in data["steps"]])