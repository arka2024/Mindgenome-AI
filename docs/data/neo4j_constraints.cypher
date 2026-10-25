// MindGenome AI — Neo4j constraints (Aura / Community, single DB)
// Apply once at worker boot (idempotent CREATE CONSTRAINT IF NOT EXISTS).

CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.user_id IS UNIQUE;

CREATE CONSTRAINT document_tenant_unique IF NOT EXISTS
FOR (d:Document) REQUIRE (d.user_id, d.document_id) IS UNIQUE;

CREATE CONSTRAINT chapter_tenant_unique IF NOT EXISTS
FOR (c:Chapter) REQUIRE (c.user_id, c.chapter_id) IS UNIQUE;

CREATE CONSTRAINT chunk_tenant_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE (c.user_id, c.chunk_id) IS UNIQUE;

CREATE CONSTRAINT concept_tenant_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE (c.user_id, c.concept_id) IS UNIQUE;

CREATE CONSTRAINT concept_normalized_unique IF NOT EXISTS
FOR (c:Concept) REQUIRE (c.user_id, c.normalized_name) IS UNIQUE;

CREATE CONSTRAINT question_tenant_unique IF NOT EXISTS
FOR (q:Question) REQUIRE (q.user_id, q.question_id) IS UNIQUE;

CREATE INDEX concept_name_idx IF NOT EXISTS
FOR (c:Concept) ON (c.user_id, c.name);

CREATE INDEX prereq_confidence_idx IF NOT EXISTS
FOR ()-[r:PREREQUISITE_OF]-() ON (r.confidence);

CREATE INDEX struggles_user_idx IF NOT EXISTS
FOR ()-[r:STRUGGLES_WITH]-() ON (r.since);
