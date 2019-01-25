DROP TABLE IF EXISTS geek;

CREATE TABLE geeks (
  id TEXT PRIMARY KEY,
  pronoun TEXT DEFAULT "human meatsack",
  username TEXT,
  onlunch INTEGER NOT NULL DEFAULT 0
);
