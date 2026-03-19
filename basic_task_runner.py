from render_sdk import RenderAsync
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def trigger_task_run():

  render = RenderAsync()

  started_run = await render.workflows.start_task(
    "render-workflows-test/calculate_square",
    [2]
  )

  print(f"Task run started: {started_run.id}")
  print(f"Initial status: {started_run.status}")

  finished_run = await started_run

  print(f"Task run completed: {finished_run.id}")
  print(f"Final status: {finished_run.status}")

if __name__ == "__main__":
  asyncio.run(trigger_task_run())