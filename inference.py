import asyncio
import os
import textwrap
import json
import logging
from typing import List, Optional, Dict, Any

from openai import OpenAI
import httpx

# Required Environment Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")

# For the environment HTTP interaction (defaults to the deployed openenv space)
# During local validation, validate-submission.sh might set ENV_BASE_URL
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

def print_start(task_name: str, env_name: str, model_name: str):
    print(f"[START] task={task_name} env={env_name} model={model_name}", flush=True)

def print_step(step: int, action: str, reward: float, done: bool, error_msg: Optional[str]):
    done_str = "true" if done else "false"
    err_str = error_msg if error_msg else "null"
    # Action string might have spaces, making it a bit tricky, but we follow the exact requested format
    reward_str = f"{reward:.2f}"
    print(f"[STEP] step={step} action={action} reward={reward_str} done={done_str} error={err_str}", flush=True)

def print_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    score_str = f"{score:.2f}"
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])
    print(f"[END] success={success_str} steps={steps} score={score_str} rewards={rewards_str}", flush=True)

SYSTEM_PROMPT = """
You are a fraud detection investigator AI.
You have access to several actions according to the OpenEnv 'gov-fraud-detection' environment.
Please respond using JSON representing the action to take.
Actions available:
- read_document(document_id)
- flag_duplicate(entity_ids)
- flag_shell_company(entity_ids) 
- trace_ownership(entity_ids)
- flag_overbilling(entity_ids)
- submit_finding(finding_type, defendant, amount_at_risk, legal_basis, evidence, reasoning)

Example Response:
{"action": "read_document", "parameters": {"document_id": "doc_123"}}
"""

async def main():
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN or "dummy_token"
    )

    tasks_to_run = ["duplicate_billing", "shell_company", "fca_complaint"]
    benchmark_name = "gov-fraud-detection"
    
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        for task_name in tasks_to_run:
            print_start(task_name=task_name, env_name=benchmark_name, model_name=MODEL_NAME)
            
            done = False
            step_count = 0
            rewards = []
            score = 0.0
            success = False
            last_cumulative_reward = 0.0

            try:
                # 1. Reset environment
                reset_res = await http_client.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_name})
                reset_res.raise_for_status()
                state = reset_res.json()
            except Exception as e:
                print_step(1, "reset_env", 0.0, True, f"Failed to reset: {e}")
                print_end(False, 1, 0.0, [0.0])
                continue

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Max steps safe bound depending on the task
            while not done and step_count < 15:
                step_count += 1
                
                # Append environment state to user prompt
                messages.append({"role": "user", "content": f"Current State:\\n{json.dumps(state)}"})
                
                action_str = "no_action"
                reward = 0.0
                error_msg = None
                
                try:
                    completion = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=messages,
                        temperature=0.0
                    )
                    
                    llm_response = completion.choices[0].message.content or ""
                    messages.append({"role": "assistant", "content": llm_response})
                    
                    # Parse LLM response
                    cleaned_resp = llm_response.strip()
                    if cleaned_resp.startswith("```json"):
                        cleaned_resp = cleaned_resp[7:].strip()
                    if cleaned_resp.endswith("```"):
                        cleaned_resp = cleaned_resp[:-3].strip()
                        
                    try:
                        action_payload = json.loads(cleaned_resp)
                        action_str = f"{action_payload.get('action', 'unknown')}({list(action_payload.get('parameters', {}).values())})"
                    except json.JSONDecodeError:
                        action_payload = {"action": "invalid_format", "parameters": {"raw": llm_response}}
                        action_str = "invalid_format"
                    
                    # 2. Step environment
                    step_res = await http_client.post(f"{ENV_BASE_URL}/step", json=action_payload)
                    step_res.raise_for_status()
                    
                    state = step_res.json()
                    
                    done = state.get("done", False)
                    error_msg = state.get("last_action_error", None)
                    current_cumulative = state.get("cumulative_reward", 0.0)
                    
                    reward = current_cumulative - last_cumulative_reward
                    last_cumulative_reward = current_cumulative

                except Exception as e:
                    error_msg = str(e)
                    done = True

                rewards.append(reward)
                # Clean up error_msg to avoid newlines breaking stdout format
                if error_msg:
                    error_msg = error_msg.replace("\n", " ").replace("\r", "")
                print_step(step_count, action_str.replace("\n", ""), reward, done, error_msg)

            # 3. Retrieve final state for score
            try:
                state_res = await http_client.get(f"{ENV_BASE_URL}/state")
                state_res.raise_for_status()
                final_state = state_res.json()
                score = final_state.get("score", 0.0)
                
                # Check mapping against YAML thresholds
                thresholds = {"duplicate_billing": 0.70, "shell_company": 0.60, "fca_complaint": 0.50}
                success = score >= thresholds.get(task_name, 0.0)
            except Exception:
                pass

            print_end(success, step_count, score, rewards)

if __name__ == "__main__":
    asyncio.run(main())
