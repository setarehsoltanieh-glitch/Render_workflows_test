from render_sdk import Workflows, RenderAsync
from pydantic import BaseModel

from tools import search_web, search_reddit, generate_report, write_file, create_plan
from models import Plan


TOOL_MAP = {
    "search_web": search_web,
    "search_reddit": search_reddit,
    "generate_report": generate_report,
    "write_file": write_file,
}
render = RenderAsync()

class PlannerWorkflow:

    async def run(self, user_goal: str) -> str:
        plan: Plan = await render.workflows.start_task(
            create_plan,
            user_goal,
        )

        results: dict[str, str] = {}

        for step in plan.steps:
            params = step.params
            for tool, result in results.items():
                params = params.replace(f"{{{{{tool}_result}}}}", result)
            result: str = await render.workflows.start_task(
                TOOL_MAP[step.tool],
                params,
            )
            results[step.tool] = result

        last_result = results.get(plan.steps[-1].tool, "No steps were executed.")
        return f"Done after {len(plan.steps)} step(s). Last result: {last_result}"
