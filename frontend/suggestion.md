The Compromise: "RAG-Assisted" Deterministic Grading
If you ever want to fix the "brittleness" of your current system (where it fails an agent because it used a synonym for a name) without introducing LLM bias, you could use NLP tools like Semantic Similarity (Cosine Similarity) instead.

Instead of writing: if "williams" in report:

You would convert the agent's answer into embeddings and check if it means the same thing as the ground truth. This gives you exact, mathematical grading without forcing the LLM to guess the exact exact keyword you typed in the code!

1. Separate "Reasoning" from "Action" (Thought Trajectories)
Currently, if an agent fails, it's hard to know why it failed.

The Idea: Update the Action Pydantic model to require a scratchpad or thought field before the actual action.
Example: {"thought": "I see FastBuild LLC, let me check its parent", "action_type": "trace_ownership", ...}
Why it's great: When you save these logs to your Database, you can read exactly what the LLM was getting confused by. Furthermore, you can use these logs for "Chain-of-Thought DPO" (Direct Preference Optimization), rewarding models that show better investigative logic.

1. "Multi-Hop" External Pinging (The Subpoena Mechanic)
In real life, investigators don’t have all the documents on day one.

The Idea: Make the request_more_docs action actually do something. Hide the crucial final piece of evidence (like the Bank Statement for the Shell Company task). The agent must find enough preliminary evidence to confidently call request_more_docs(target="FastBuild LLC bank records").
Mechanic: This action could cost 3 "Steps" to simulate legal delay, but it pushes the critical document into the available_documents array. This tests the agent's ability to plan ahead and wait for evidence.

To make the "Investigation Budget" and "Context Stress Test" (Noise) mechanic actually work, you are completely right—you must update the system prompt to let the LLM know the rules of the game. You would change the prompt in inference.py to look like this:

python
STRATEGY:

- You are working under a strict investigation budget.
- You have 10 maximum steps.
- Some documents in this file system are irrelevant noise (e.g., employee handbooks).
- WARNING: Every time you use `read_document`, it costs -0.01 from your final score.
- Do not brute-force read every file. Carefully read the `available_documents` previews and ONLY open the documents you suspect contain critical fraud evidence.
Why this is the core of AI Training (RLHF / PPO)
When you train a model using RL (Reinforcement Learning), the model starts by guessing.

Episode 1: It reads all 50 noise documents. Its final score is 0.0 because it ran out of steps and hit the budget penalties.
Episode 500: Through gradient descent, the model's neural weights adjust to realize, "Wait, the prompt told me to look at the previews. Every time I open a file that doesn't say 'Medicare Claim' in the title, my reward goes down."
Episode 5,000: The model learns to completely ignore the distraction documents, perfectly optimizing its token use and actions to match the prompt's instructions.

The Missing Piece for "Proper" Training
To make this train an LLM that is actually smart, you just need to change one thing: the static file data/documents.py must become a dynamic Python function.

Right now you have:

python

# data/documents.py

TASK1_DOCUMENTS = {
   "CLAIM-001": {"patient": "John Doe", "amount": 1500},
   "CLAIM-002": {"patient": "John Doe", "amount": 1500}
}
TASK1_GROUND_TRUTH = {"exact_duplicates": [("CLAIM-001", "CLAIM-002")]}
To make it train properly, you need to rewrite it so that every time env.reset() is called, the names, numbers, and Claim IDs are randomly generated:

python

# procedural_generator.py

import random
def generate_task1_episode():
    # Randomize the names and transaction IDs every single time
    fake_name = random.choice(["John Doe", "Alice Smith", "Bob Jones"])
    fake_amount = random.randint(1000, 5000)
    fake_claim_id_1 = f"CLAIM-{random.randint(1000,9999)}"
    fake_claim_id_2 = f"CLAIM-{random.randint(1000,9999)}"

    docs = {
       fake_claim_id_1: {"patient": fake_name, "amount": fake_amount},
       fake_claim_id_2: {"patient": fake_name, "amount": fake_amount}
    }
    
    # Generate the ground truth dynamically based on the random IDs
    truth = {"exact_duplicates": [(fake_claim_id_1, fake_claim_id_2)]}
    
    return docs, truth
The Verdict
Is the architecture good? Yes, the dense reward functions, loop penalties, and hallucination penalties are top-tier.
Will it train? Yes, the math is solid.
What needs to change? You must introduce randomization (Procedural Data Generation) to your documents so the LLM has to read the text and do the logic every time, rather memorizing a static dictionary.
If you add that one randomization layer, you will have a world-class training environment.
