# Reward Mechanism Analysis: Medium vs. Hard Tasks

This report analyzes the reward distribution and presentation logic for the **Shell Company (Medium)** and **FCA Complaint (Hard)** tasks within the metaXsst environment.

## 1. Logic Comparison (Backend)

| Feature | Shell Company (Medium) | FCA Complaint (Hard) |
| :--- | :--- | :--- |
| **Primary Goal** | Ownership Traversal | Legal Case Synthesis |
| **Key Reward Driver** | **Ownership Hops (70%)**: Incremental rewards for each parent/child link found. | **Case Structure (40%)**: Correct Defendant and Violation Type. |
| **Evidence Weight** | 15% (3+ key docs cited) | 25% (3+ key docs cited) |
| **Quantification** | 5% (+/- 15% range) | 15% (Strict range match) |
| **Hallucination Check** | Light | **Heavy**: -0.10 per hallucinated doc ID. |
| **Bonuses** | N/A | **Scheme Identification (5%)**: "upcoding" keyword search. |

### **Key Difference: Reward Density**
The **Medium task** is designed with "stepped" progression rewards. Agents are guided through the ownership chain hop-by-hop. The **Hard task** is more "terminal-weighted"—while document reading gives small rewards, the majority of the score depends on the final, accurately structured complaint.

---

## 2. UI Presentation (Frontend)

Based on browser analysis of the running dashboard:

### **Presentation Mode**
- **Cumulative Only:** The UI displays a single rolling score in the session header (e.g., `+0.450`).
- **Dynamic Feedback:** Reward values update instantly following a `step` API call.
- **Visual Cues:** The "Confidence" progress bar in the header maps to the cumulative reward percentage, turning from blue to emerald when the score passes a success threshold (>60%).

### **UI Strengths & Gaps**
- **Strength:** The dense scaling is visible—performing a "Read" action in the Hard task provides a higher numerical increment (+0.030) than in the Medium task (+0.012), signaling higher risk/reward.
- **Gap:** The **Reward Breakdown** is currently hidden. The agent or user cannot see *which* specific components (e.g., "Hop 1" or "Defendant Correct") contributed to the current score without checking the `/state` API directly.

---

## 3. Recommended UI Enhancements

To improve the training feedback loop for AI agents and human oversight:
1. **Interactive Breakdown:** Clicking the Reward Pill should open a tooltip showing the Pydantic `breakdown` dictionary returned by the grader.
2. **Action-Reward Log:** Add a small toast or log entry in the Action Terminal saying: `[Action] Trace Ownership: +0.20 (Hop 1 Traced)`.
3. **Penalty Visualization:** Use red text transitions for the reward counter when a hallucination or loop penalty is applied.

---
**Analysis performed by Antigravity AI**
