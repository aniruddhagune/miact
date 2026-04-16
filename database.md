CREATE TABLE entities (
    entity_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,

    entity_type TEXT,
    parent_id INT REFERENCES entities(entity_id)
);

CREATE TABLE sources (
    source_id SERIAL PRIMARY KEY,
    name TEXT,
    base_url TEXT UNIQUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    published_at TIMESTAMP
);

CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,   -- URL

    source_id INT REFERENCES sources(source_id),
    title TEXT,

    domain_type TEXT,  -- NEW (product / news)

    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE queries (
    query_id SERIAL PRIMARY KEY,
    session_id INT REFERENCES sessions(session_id),

    query_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE facts (
    fact_id SERIAL PRIMARY KEY,

    entity_id INT REFERENCES entities(entity_id),  -- NOW OPTIONAL
    document_id TEXT REFERENCES documents(document_id),

    aspect TEXT NOT NULL,
    value TEXT,
    unit TEXT,
    attr_type TEXT,

    confidence_score FLOAT DEFAULT 1.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE opinions (
    opinion_id SERIAL PRIMARY KEY,

    entity_id INT REFERENCES entities(entity_id),  -- NOW OPTIONAL
    document_id TEXT REFERENCES documents(document_id),

    aspect TEXT,
    opinion_text TEXT,

    sentiment_label TEXT,
    sentiment_score FLOAT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);