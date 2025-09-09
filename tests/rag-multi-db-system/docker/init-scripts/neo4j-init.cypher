CREATE CONSTRAINT ON (d:Document) ASSERT d.document_id IS UNIQUE;
CREATE CONSTRAINT ON (e:Entity) ASSERT e.entity_id IS UNIQUE;

CREATE INDEX ON :Document(title);
CREATE INDEX ON :Document(created_at);
CREATE INDEX ON :Entity(entity_type);
CREATE INDEX ON :Entity(created_at);