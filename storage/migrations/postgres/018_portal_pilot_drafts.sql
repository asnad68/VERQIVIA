-- VERQIVIA PostgreSQL schema v18: private, authenticated pilot intake drafts.
CREATE TABLE IF NOT EXISTS portal_pilot_drafts (
    draft_id UUID PRIMARY KEY,
    actor TEXT NOT NULL CHECK (btrim(actor) <> ''),
    idempotency_key TEXT NOT NULL CHECK (btrim(idempotency_key) <> ''),
    request_sha256 TEXT NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
    payload_json JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'RECEIVED'
        CHECK (status IN ('RECEIVED', 'UNDER_REVIEW', 'ACCEPTED', 'DECLINED')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (actor, idempotency_key),
    UNIQUE (actor, draft_id)
);

CREATE INDEX IF NOT EXISTS idx_portal_pilot_drafts_actor_recorded
    ON portal_pilot_drafts(actor, recorded_at DESC);

REVOKE ALL ON portal_pilot_drafts FROM PUBLIC;
GRANT SELECT, INSERT ON portal_pilot_drafts TO nothing_app;
REVOKE UPDATE, DELETE ON portal_pilot_drafts FROM nothing_app, nothing_payment;

ALTER TABLE portal_pilot_drafts OWNER TO nothing_migrator;
