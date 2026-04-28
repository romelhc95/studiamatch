import sys
import json
import subprocess
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("WorkerRunner")

def run_worker():
    if len(sys.argv) < 3:
        logger.error("Usage: python worker_runner.py <worker_id> <json_plan_path>")
        sys.exit(1)

    worker_id = int(sys.argv[1])
    json_file = sys.argv[2]

    if not os.path.exists(json_file):
        logger.error(f"Plan file not found: {json_file}")
        sys.exit(1)

    with open(json_file, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    # Find tasks for this worker
    worker_tasks = []
    for assignment in plan.get("worker_assignments", []):
        if assignment.get("worker_id") == worker_id:
            worker_tasks = assignment.get("tasks", [])
            break

    if not worker_tasks:
        logger.info(f"No tasks assigned to Worker {worker_id}.")
        return

    logger.info(f"Worker {worker_id} starting {len(worker_tasks)} tasks.")

    any_failed = False
    for task in worker_tasks:
        name = task.get("name")
        script = task.get("harvester_script")
        
        logger.info(f"Executing task for: {name} using {script}")
        
        try:
            # Pass institution JSON as a single string argument if universal, 
            # or just run it if dedicated (the scripts handle both cases)
            inst_json = json.dumps(task)
            
            # Execute script
            result = subprocess.run(
                ["python", script],
                capture_output=True,
                text=True,
                env={**os.environ, "SCRAPER_TASK": inst_json}
            )
            
            if result.returncode == 0:
                logger.info(f"Completed task for {name}")
            else:
                logger.error(f"Failed task for {name}. Exit code: {result.returncode}")
                logger.error(f"Output: {result.stdout}")
                logger.error(f"Error: {result.stderr}")
                any_failed = True
                
        except Exception as e:
            logger.error(f"Exception during task for {name}: {e}")
            any_failed = True

    if any_failed:
        logger.error(f"Worker {worker_id} finished with errors.")
        sys.exit(1)
    
    logger.info(f"Worker {worker_id} finished all tasks successfully.")

if __name__ == "__main__":
    run_worker()
