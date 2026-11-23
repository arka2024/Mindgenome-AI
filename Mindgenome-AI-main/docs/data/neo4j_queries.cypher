// All queries require $user_id. Repositories must not expose a query without it.

// ---------------------------------------------------------------------------
// Prerequisite chain of a concept (ancestors: must-learn-first)
// A -[:PREREQUISITE_OF]-> B means A precedes B.
// ---------------------------------------------------------------------------
MATCH (target:Concept {user_id: $user_id, concept_id: $concept_id})
MATCH (anc:Concept {user_id: $user_id})-[r:PREREQUISITE_OF]->(mid:Concept {user_id: $user_id})
WHERE r.user_id = $user_id
  AND r.status <> 'rejected'
  AND (r.status = 'confirmed' OR r.confidence >= $min_confidence)
  AND (mid = target OR EXISTS {
        MATCH (mid)-[:PREREQUISITE_OF*1..8]->(target)
        WHERE ALL(rel IN relationships(.) WHERE rel.user_id = $user_id AND rel.status <> 'rejected'
          AND (rel.status = 'confirmed' OR rel.confidence >= $min_confidence))
      })
WITH DISTINCT anc, r
RETURN anc.concept_id AS concept_id, anc.name AS name, r.confidence AS via_confidence
ORDER BY anc.name;

// ---------------------------------------------------------------------------
// Weakest ancestor (for remedial targeting)
// $weak_ids is the set of concept_ids with Postgres band=beginner AND n>=3
// ---------------------------------------------------------------------------
MATCH (target:Concept {user_id: $user_id, concept_id: $concept_id})
MATCH path = (weak:Concept {user_id: $user_id})-[:PREREQUISITE_OF*1..8]->(target)
WHERE weak.concept_id IN $weak_ids
  AND ALL(n IN nodes(path) WHERE n.user_id = $user_id)
  AND ALL(rel IN relationships(path) WHERE rel.user_id = $user_id AND rel.status <> 'rejected'
    AND (rel.status = 'confirmed' OR rel.confidence >= $min_confidence))
WITH weak, length(path) AS dist
RETURN weak.concept_id AS concept_id, weak.name AS name, dist
ORDER BY dist DESC, weak.name
LIMIT 1;

// ---------------------------------------------------------------------------
// Shortest remedial path: weak ancestor → target, high-confidence prereqs only
// ---------------------------------------------------------------------------
MATCH (start:Concept {user_id: $user_id, concept_id: $start_id}),
      (goal:Concept {user_id: $user_id, concept_id: $goal_id})
MATCH path = shortestPath((start)-[:PREREQUISITE_OF*1..12]->(goal))
WHERE ALL(n IN nodes(path) WHERE n.user_id = $user_id)
  AND ALL(rel IN relationships(path) WHERE rel.user_id = $user_id AND rel.status <> 'rejected'
    AND (rel.status = 'confirmed' OR rel.confidence >= $min_confidence))
RETURN [n IN nodes(path) | n.concept_id] AS concept_ids,
       [n IN nodes(path) | n.name] AS names,
       length(path) AS hops;

// ---------------------------------------------------------------------------
// Next-concept candidates: no unmastered high-confidence prerequisite
// $ready_ids = concepts with band in (proficient, mastered) OR unseen leaves
// $blocked_parent_ids = beginner with evidence
// ---------------------------------------------------------------------------
MATCH (c:Concept {user_id: $user_id})
WHERE c.concept_id IN $candidate_ids
  AND NOT EXISTS {
        MATCH (p:Concept {user_id: $user_id})-[r:PREREQUISITE_OF]->(c)
        WHERE r.user_id = $user_id
          AND r.status <> 'rejected'
          AND (r.status = 'confirmed' OR r.confidence >= $min_confidence)
          AND p.concept_id IN $blocked_parent_ids
      }
RETURN c.concept_id AS concept_id, c.name AS name
ORDER BY c.name;

// ---------------------------------------------------------------------------
// Dashboard subgraph (bounded)
// ---------------------------------------------------------------------------
MATCH (u:User {user_id: $user_id})-[:OWNS]->(c:Concept {user_id: $user_id})
WITH c LIMIT 200
OPTIONAL MATCH (c)-[r:PREREQUISITE_OF|RELATED_TO|USES]->(o:Concept {user_id: $user_id})
WHERE r.user_id = $user_id AND r.status <> 'rejected'
OPTIONAL MATCH (u2:User {user_id: $user_id})-[s:STRUGGLES_WITH]->(c)
RETURN collect(DISTINCT c) AS concepts,
       collect(DISTINCT {from: c.concept_id, to: o.concept_id, type: type(r), confidence: r.confidence}) AS edges,
       collect(DISTINCT s) AS struggle_flags;

// ---------------------------------------------------------------------------
// Cycle guard before writing A -[:PREREQUISITE_OF]-> B
// If this returns a row, abort the write.
// ---------------------------------------------------------------------------
MATCH (b:Concept {user_id: $user_id, concept_id: $b_id})
MATCH path = (b)-[:PREREQUISITE_OF*1..16]->(a:Concept {user_id: $user_id, concept_id: $a_id})
WHERE ALL(n IN nodes(path) WHERE n.user_id = $user_id)
  AND ALL(rel IN relationships(path) WHERE rel.user_id = $user_id)
RETURN true AS would_cycle LIMIT 1;
