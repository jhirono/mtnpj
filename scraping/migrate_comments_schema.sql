PRAGMA foreign_keys = 0;

CREATE TABLE comments_new (
  comment_id TEXT PRIMARY KEY,
  parent_id TEXT NOT NULL,
  parent_type TEXT NOT NULL CHECK(parent_type IN ('route', 'area', 'tick')),
  comment_author TEXT,
  comment_text TEXT,
  comment_time TEXT
);

INSERT INTO comments_new SELECT * FROM comments;
DROP TABLE comments;
ALTER TABLE comments_new RENAME TO comments;

CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id, parent_type);

PRAGMA foreign_keys = 1;
