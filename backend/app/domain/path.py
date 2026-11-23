from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class NextRecommendation:
    mode: str  # "learn", "remedial", "revision", "retest"
    concept_id: str | None
    concept_name: str
    because: str


@dataclass
class PathItem:
    concept_id: str
    name: str
    because: str
    kind: str  # "learn", "remedial", "retest", "revision", "next"
    band: str | None = None


def determine_next_step(
    target_concept_id: str,
    target_concept_name: str,
    target_score: float,
    ancestor_concepts: list[dict[str, Any]],  # [{id, name, mastery, band, n}]
    descendant_concepts: list[dict[str, Any]],
) -> NextRecommendation:
    """
    Determine the next learning action using knowledge graph prerequisites and mastery.
    """
    # 1. Check for weak ancestors that have sufficient evidence (n >= 3) and low mastery (< 55)
    weak_ancestors = [
        anc for anc in ancestor_concepts
        if anc.get("mastery", 100) < 55 and anc.get("n", 0) >= 3
    ]
    if weak_ancestors and target_score < 60:
        weakest = min(weak_ancestors, key=lambda x: x.get("mastery", 0))
        return NextRecommendation(
            mode="remedial",
            concept_id=weakest["id"],
            concept_name=weakest["name"],
            because=f"You scored low on {target_concept_name}. Weak prerequisite blocking progress: {weakest['name']}.",
        )

    # 2. If target concept was recently remediated and is improving:
    if target_score >= 61 and descendant_concepts:
        next_c = descendant_concepts[0]
        return NextRecommendation(
            mode="learn",
            concept_id=next_c["id"],
            concept_name=next_c["name"],
            because=f"Prerequisites for {next_c['name']} are ready: {target_concept_name} is now proficient.",
        )

    # 3. Target score is moderate or needs revision
    return NextRecommendation(
        mode="revision",
        concept_id=target_concept_id,
        concept_name=target_concept_name,
        because="Keep this concept in the revision loop to reinforce retention before advancing.",
    )


def plan_learning_path(
    all_concepts: list[dict[str, Any]],  # [{id, name, mastery, band, n, prerequisites: [...]}]
) -> list[PathItem]:
    """
    Construct ordered learning path items for the learner.
    """
    items: list[PathItem] = []
    for c in all_concepts:
        cid = c["id"]
        cname = c["name"]
        m = c.get("mastery", 0)
        band = c.get("band", "insufficient_evidence")

        if band == "mastered" or (band == "proficient" and m >= 70):
            items.append(PathItem(
                concept_id=cid,
                name=cname,
                because="Proficient — schedule light spaced repetition.",
                kind="revision",
                band=band,
            ))
        elif band == "beginner" or m < 55:
            items.append(PathItem(
                concept_id=cid,
                name=cname,
                because=f"Foundational topic with low mastery ({round(m)}%). Prioritize remedial study.",
                kind="remedial",
                band=band,
            ))
        else:
            items.append(PathItem(
                concept_id=cid,
                name=cname,
                because="Ready for next learning module and assessment.",
                kind="learn",
                band=band,
            ))

    # Sort so remedial comes first, then learn, then revision
    priority = {"remedial": 0, "learn": 1, "next": 2, "retest": 3, "revision": 4}
    items.sort(key=lambda x: priority.get(x.kind, 5))
    return items
