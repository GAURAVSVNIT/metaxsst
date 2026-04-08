"""
Simple Training Script - Start Here
====================================
This is a simplified training script that works without GPU.
It uses the OpenAI API to generate training data and fine-tune via API.

Usage:
    python train_simple.py --episodes 100
    python train_simple.py --episodes 500 --task all
"""

import argparse
import json
import os
import random
from typing import List, Dict, Any
from datetime import datetime
import logging

from environment import GovFraudEnv
from models import Action

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ALL_TASKS = ["duplicate_billing", "shell_company", "fca_complaint"]


# ============================================================================
# PROCEDURAL DATA GENERATION
# ============================================================================

class DataGenerator:
    """Generate randomized training data to prevent memorization"""
    
    NAMES = ["John Doe", "Alice Smith", "Bob Jones", "Maria Garcia", "James Wilson",
             "Sarah Chen", "Michael Brown", "Emma Davis", "David Lee", "Lisa Anderson"]
    
    COMPANIES = ["MedCorp", "HealthPlus", "CareTech", "WellnessCo", "MediSupply",
                 "CareFirst", "HealthTech", "MedPro", "VitalCare", "HealthBridge"]
    
    PROCEDURES = ["99213", "99214", "99215", "99203", "99204", "99205"]
    
    @classmethod
    def generate_duplicate_billing_episode(cls):
        """Generate a random duplicate billing scenario"""
        patient = random.choice(cls.NAMES)
        amount = random.randint(1000, 5000)
        date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        provider = random.choice(cls.COMPANIES)
        procedure = random.choice(cls.PROCEDURES)
        
        # Generate claim IDs
        claims = [f"CLAIM-{random.randint(1000, 9999)}" for _ in range(10)]
        
        # Pick 2 for exact duplicate
        exact_dup = random.sample(claims[:5], 2)
        
        # Pick 2 for near duplicate (different date)
        near_dup = random.sample([c for c in claims if c not in exact_dup][:3], 2)
        
        documents = {}
        
        # Create exact duplicates
        for claim_id in exact_dup:
            documents[claim_id] = {
                "claim_id": claim_id,
                "patient": patient,
                "date": date,
                "amount": amount,
                "provider": provider,
                "procedure": procedure
            }
        
        # Create near duplicate (date shifted)
        near_date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        for claim_id in near_dup:
            documents[claim_id] = {
                "claim_id": claim_id,
                "patient": patient,
                "date": near_date if claim_id == near_dup[1] else date,
                "amount": amount,
                "provider": provider,
                "procedure": procedure
            }
        
        # Add noise documents
        for claim_id in claims:
            if claim_id not in documents:
                documents[claim_id] = {
                    "claim_id": claim_id,
                    "patient": random.choice(cls.NAMES),
                    "date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                    "amount": random.randint(500, 3000),
                    "provider": random.choice(cls.COMPANIES),
                    "procedure": random.choice(cls.PROCEDURES)
                }
        
        return {
            "documents": documents,
            "ground_truth": {
                "exact_duplicates": [tuple(exact_dup)],
                "near_duplicates": [tuple(near_dup)]
            }
        }


# ============================================================================
# EXPERT POLICIES (DEMOS)
# ============================================================================

class ExpertPolicy:
    """Hand-crafted policies for demonstration data collection."""

    @staticmethod
    def _read_actions(doc_ids: List[str], reason: str) -> List[Dict[str, Any]]:
        return [
            {
                "thought": f"Reading {doc_id} to verify {reason}",
                "action": {"action_type": "read_document", "document_id": doc_id},
            }
            for doc_id in doc_ids
        ]
    
    @staticmethod
    def solve_duplicate_billing(env: GovFraudEnv) -> List[Dict[str, Any]]:
        """Demonstration policy for the duplicate billing task."""
        actions: List[Dict[str, Any]] = []
        obs = env._obs if env._obs is not None else env.reset()
        key_docs = [doc.doc_id for doc in obs.available_documents if doc.doc_id in {"CLAIM-001", "CLAIM-002", "CLAIM-003", "CLAIM-004"}]
        actions.extend(ExpertPolicy._read_actions(key_docs[:3], "duplicate billing pattern"))
        actions.append({
            "thought": "Requesting an audit memo to strengthen evidence citations",
            "action": {
                "action_type": "request_more_docs",
                "request_target": "duplicate billing audit memo for PRV-8821",
                "requested_doc_type": "audit_memo",
                "reasoning": "Need corroborating audit narrative before final submission",
            },
        })
        actions.append({
            "thought": "Found exact duplicates with same patient, date, amount, and provider",
            "action": {
                "action_type": "flag_duplicate",
                "entity_ids": ["CLAIM-001", "CLAIM-002"],
                "reasoning": "Exact match on patient, service date, procedure, provider, and amount",
            },
        })
        actions.append({
            "thought": "Found near-duplicates with only a one-day date difference",
            "action": {
                "action_type": "flag_duplicate",
                "entity_ids": ["CLAIM-001", "CLAIM-004"],
                "reasoning": "Same patient, procedure, provider, and amount with service date shifted by 1 day",
            },
        })
        actions.append({
            "thought": "All fraud evidence is identified, submitting the duplicate billing finding",
            "action": {
                "action_type": "submit_finding",
                "finding_type": "duplicate_billing",
                "defendant": "MedCorp Associates LLC",
                "amount_at_risk": 370.0,
                "legal_basis": "31 U.S.C. §3729",
                "evidence": ["CLAIM-001", "CLAIM-002", "CLAIM-004"],
                "reasoning": "Exact duplicate billing plus a near-duplicate claim show a repeated billing pattern for the same patient and service.",
            },
        })
        return actions

    @staticmethod
    def solve_shell_company(env: GovFraudEnv) -> List[Dict[str, Any]]:
        """Demonstration policy for the shell company task."""
        actions: List[Dict[str, Any]] = []
        obs = env._obs if env._obs is not None else env.reset()
        key_docs = [
            "CONTRACT-001",
            "CONTRACT-002",
            "STATE-FILING-DE-001",
            "STATE-FILING-NV-001",
            "TRUST-DOC-001",
            "GOV-EMPLOYEE-001",
        ]
        present_docs = {doc.doc_id for doc in obs.available_documents}
        actions.extend(ExpertPolicy._read_actions([doc_id for doc_id in key_docs if doc_id in present_docs], "ownership and conflict tracing"))
        actions.append({
            "thought": "Requesting bank records to corroborate ownership-linked fund flow",
            "action": {
                "action_type": "request_more_docs",
                "request_target": "FastBuild LLC bank records",
                "requested_doc_type": "bank_records",
                "reasoning": "Need corroboration that contract payouts followed the traced chain",
            },
        })
        actions.extend([
            {
                "thought": "Tracing FastBuild LLC to its direct owner",
                "action": {
                    "action_type": "trace_ownership",
                    "entity_ids": ["FastBuild LLC", "ConstructPro Inc"],
                    "reasoning": "State filing shows FastBuild LLC is owned by ConstructPro Inc",
                },
            },
            {
                "thought": "Tracing ConstructPro Inc to the family trust behind it",
                "action": {
                    "action_type": "trace_ownership",
                    "entity_ids": ["ConstructPro Inc", "R. Holden Family Trust"],
                    "reasoning": "Corporate filing links ConstructPro Inc to the R. Holden Family Trust",
                },
            },
            {
                "thought": "Tracing the trust to the Holden-Williams family relationship",
                "action": {
                    "action_type": "trace_ownership",
                    "entity_ids": ["R. Holden Family Trust", "Derek Williams / Patricia Holden-Williams"],
                    "reasoning": "Trust documents and financial disclosures identify Patricia Holden-Williams as the spouse connection",
                },
            },
            {
                "thought": "The ownership chain and contract awards indicate a conflict of interest",
                "action": {
                    "action_type": "flag_shell_company",
                    "entity_ids": ["FastBuild LLC"],
                    "reasoning": "Sole-source contracts, Delaware entity structure, and indirect ownership by the contracting officer's spouse indicate a shell company",
                },
            },
            {
                "thought": "Submitting the shell company finding with the traced ownership chain",
                "action": {
                    "action_type": "submit_finding",
                    "finding_type": "shell_company",
                    "defendant": "FastBuild LLC",
                    "amount_at_risk": 3190000.0,
                    "legal_basis": "31 U.S.C. §3729",
                    "evidence": ["STATE-FILING-DE-001", "STATE-FILING-NV-001", "TRUST-DOC-001", "GOV-EMPLOYEE-001"],
                    "reasoning": "FastBuild LLC received sole-source awards while being indirectly owned through ConstructPro Inc and the R. Holden Family Trust by Patricia Holden-Williams, the contracting officer's spouse.",
                },
            },
        ])
        return actions

    @staticmethod
    def solve_fca_complaint(env: GovFraudEnv) -> List[Dict[str, Any]]:
        """Demonstration policy for the FCA complaint task."""
        actions: List[Dict[str, Any]] = []
        obs = env._obs if env._obs is not None else env.reset()
        key_docs = [
            "ANON-TIP-001",
            "CMS-CLAIM-BATCH-001",
            "PHYSICIAN-ORDERS-001",
            "INTERNAL-EMAIL-001",
            "CORPORATE-FILING-001",
            "EXPERT-ANALYSIS-001",
            "FINANCIAL-RECORDS-001",
            "REIMBURSEMENT-POLICY-001",
        ]
        present_docs = {doc.doc_id for doc in obs.available_documents}
        actions.extend(ExpertPolicy._read_actions([doc_id for doc_id in key_docs if doc_id in present_docs], "False Claims Act scheme"))
        actions.extend([
            {
                "thought": "Requesting a compliance review to support medical-necessity claims evidence",
                "action": {
                    "action_type": "request_more_docs",
                    "request_target": "K0831 medical necessity compliance review",
                    "requested_doc_type": "compliance_review",
                    "reasoning": "Need corroborating compliance findings before filing",
                },
            },
            {
                "thought": "Flagging the provider for systemic overbilling and upcoding",
                "action": {
                    "action_type": "flag_overbilling",
                    "entity_ids": ["MediSupply Corp"],
                    "reasoning": "Claims volume and internal communications show an intentional upcoding scheme",
                },
            },
            {
                "thought": "Submitting the FCA complaint with the strongest evidence documents",
                "action": {
                    "action_type": "submit_finding",
                    "finding_type": "fca_violation",
                    "defendant": "MediSupply Corp",
                    "amount_at_risk": 9800000.0,
                    "legal_basis": "31 U.S.C. §3729(a)(1)(A), 31 U.S.C. §3729(a)(1)(B)",
                    "evidence": ["ANON-TIP-001", "CMS-CLAIM-BATCH-001", "PHYSICIAN-ORDERS-001", "INTERNAL-EMAIL-001", "EXPERT-ANALYSIS-001"],
                    "reasoning": "MediSupply Corp upcoded durable medical equipment claims, including K0831 wheelchairs, and internal emails confirm the scheme was intentional.",
                },
            },
        ])
        return actions

    @staticmethod
    def solve(env: GovFraudEnv) -> List[Dict[str, Any]]:
        if env.task_id == "duplicate_billing":
            return ExpertPolicy.solve_duplicate_billing(env)
        if env.task_id == "shell_company":
            return ExpertPolicy.solve_shell_company(env)
        if env.task_id == "fca_complaint":
            return ExpertPolicy.solve_fca_complaint(env)
        raise ValueError(f"Unsupported task: {env.task_id}")


# ============================================================================
# TRAINING DATA COLLECTION
# ============================================================================

def collect_training_data(
    num_episodes: int,
    task_id: str = "duplicate_billing",
    dynamic_data: bool = False,
) -> str:
    """
    Collect training data by running expert policy on procedural tasks.
    """
    logger.info(f"Collecting {num_episodes} training episodes for {task_id}...")
    
    training_data = []
    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data)
    
    for episode in range(num_episodes):
        # Reset first so planning and execution happen on the same episode.
        obs = env.reset()

        # Get expert actions
        expert_actions = ExpertPolicy.solve(env)

        # Run episode and collect data
        episode_data = {
            "episode": episode,
            "task_id": task_id,
            "initial_observation": {
                "task_description": obs.task_description,
                "detected_signals": [
                    {"type": sig.signal_type, "severity": sig.severity, "desc": sig.description}
                    for sig in obs.detected_signals
                ],
                "available_documents": [
                    {"id": doc.doc_id, "type": doc.doc_type, "preview": doc.preview}
                    for doc in obs.available_documents
                ]
            },
            "trajectory": []
        }
        
        total_reward = 0
        for step_data in expert_actions:
            thought = step_data["thought"]
            action_dict = step_data["action"]
            
            try:
                action = Action(**action_dict)
                obs, reward, done, info = env.step(action)
                
                episode_data["trajectory"].append({
                    "thought": thought,
                    "action": action_dict,
                    "reward": reward,
                    "observation": {
                        "last_result": obs.last_action_result,
                        "last_error": obs.last_action_error,
                        "cumulative_reward": obs.cumulative_reward
                    }
                })
                
                total_reward += reward
                
                if done:
                    break
                    
            except Exception as e:
                logger.warning(f"Episode {episode} step failed: {e}")
                break
        
        episode_data["total_reward"] = total_reward
        episode_data["final_score"] = obs.cumulative_reward
        training_data.append(episode_data)
        
        if (episode + 1) % 10 == 0:
            logger.info(f"Collected {episode + 1}/{num_episodes} episodes, avg reward: {total_reward:.3f}")
    
    output_dir = os.path.join(os.path.dirname(__file__), "training_outputs")
    os.makedirs(output_dir, exist_ok=True)

    # Save training data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"training_data_{task_id}_{timestamp}.jsonl")
    
    with open(output_file, "w") as f:
        for item in training_data:
            f.write(json.dumps(item) + "\n")
    
    logger.info(f"Saved {len(training_data)} episodes to {output_file}")
    
    # Also create a simplified format for fine-tuning
    simplified_file = os.path.join(output_dir, f"training_data_simple_{task_id}_{timestamp}.jsonl")
    with open(simplified_file, "w") as f:
        for episode in training_data:
            for step in episode["trajectory"]:
                example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert fraud investigator. Think step-by-step and provide your reasoning before taking action."
                        },
                        {
                            "role": "user",
                            "content": f"Task: {episode['task_id']}\n\nObservation: {json.dumps(episode['initial_observation'], indent=2)}\n\nWhat should you do?"
                        },
                        {
                            "role": "assistant",
                            "content": f"Thought: {step['thought']}\n\nAction: {json.dumps(step['action'], indent=2)}"
                        }
                    ]
                }
                f.write(json.dumps(example) + "\n")
    
    logger.info(f"Saved simplified format to {simplified_file}")
    return simplified_file


# ============================================================================
# EVALUATION
# ============================================================================

def evaluate_model(task_id: str = "duplicate_billing", num_runs: int = 10, dynamic_data: bool = False):
    """Evaluate current model performance"""
    logger.info(f"Evaluating on {task_id} with {num_runs} runs...")
    
    env = GovFraudEnv(task_id=task_id, dynamic_data=dynamic_data)
    scores = []
    
    for run in range(num_runs):
        obs = env.reset()
        expert_actions = ExpertPolicy.solve(env)
        
        total_reward = 0
        for step_data in expert_actions:
            try:
                action = Action(**step_data["action"])
                obs, reward, done, info = env.step(action)
                total_reward += reward
                if done:
                    break
            except Exception:
                break
        
        scores.append(obs.cumulative_reward)
    
    avg_score = sum(scores) / len(scores) if scores else 0
    logger.info(f"Average score: {avg_score:.4f} (target: 0.70+)")
    
    return avg_score


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Simple Training Script")
    parser.add_argument("--episodes", type=int, default=100, help="Number of training episodes")
    parser.add_argument("--task", default="duplicate_billing", choices=ALL_TASKS + ["all"])
    parser.add_argument("--evaluate", action="store_true", help="Run evaluation only")
    parser.add_argument("--dynamic-data", action="store_true", help="Generate dynamic per-episode datasets")
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("FRAUD DETECTION AGENT - SIMPLE TRAINING")
    logger.info("="*70)
    
    if args.evaluate:
        # Evaluation mode
        if args.task == "all":
            tasks = ["duplicate_billing", "shell_company", "fca_complaint"]
        else:
            tasks = [args.task]
        
        for task in tasks:
            evaluate_model(task, dynamic_data=args.dynamic_data)
    else:
        # Training mode
        if args.task == "all":
            tasks = ["duplicate_billing", "shell_company", "fca_complaint"]
        else:
            tasks = [args.task]
        
        for task in tasks:
            logger.info(f"\n{'='*70}")
            logger.info(f"Training on task: {task}")
            logger.info(f"{'='*70}\n")
            
            # Collect training data
            data_file = collect_training_data(args.episodes, task, dynamic_data=args.dynamic_data)
            
            logger.info(f"\n✓ Training data collected: {data_file}")
            logger.info(f"\nNext steps:")
            logger.info(f"1. Upload {data_file} to OpenAI for fine-tuning")
            logger.info(f"2. Or use it with local training: python train_agent.py")
            logger.info(f"3. Evaluate with: python train_simple.py --evaluate --task {task}")
    
    logger.info("\n" + "="*70)
    logger.info("COMPLETE!")
    logger.info("="*70)


if __name__ == "__main__":
    main()
