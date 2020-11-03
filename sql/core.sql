--
-- core.sql - Core database structures for vm.utu.fi site
--
-- 2020-09-10   Add 'upload' table (STILL UNUSED!).
-- 2020-09-11   Removed type and host_architecture CHECK constraint from 'file'
-- 2020-09-26   Reduced into 'sql/core.sql'
--
CREATE TABLE teacher
(
    uid                 TEXT        NOT NULL PRIMARY KEY,
    created             TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              TEXT        NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'inactive'))
);
-- NOT USED (file.host_architecture is NULL column for now)
CREATE TABLE host_architecture
(
    type                TEXT        NOT NULL PRIMARY KEY,
    description         TEXT        NOT NULL,
    UNIQUE (description)
);
CREATE TABLE file
(
    id                  INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name                TEXT        NOT NULL UNIQUE,
    size                INTEGER     NOT NULL,
    sha1                TEXT            NULL,
    type                TEXT        NOT NULL,
    label               TEXT        NOT NULL,
    version             TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now')),
    host_architecture   TEXT            NULL,
    ostype              TEXT            NULL,
    description         TEXT            NULL,
    ram                 TEXT            NULL,
    cores               TEXT            NULL,
    disksize            TEXT            NULL,
    dtap                TEXT        NOT NULL DEFAULT 'production',
    created             TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner               TEXT        NOT NULL,
    downloadable_to     TEXT        NOT NULL DEFAULT 'nobody',
    FOREIGN KEY (owner) REFERENCES teacher (uid),
    FOREIGN KEY (host_architecture) REFERENCES host_architecture (type),
    UNIQUE (label, version, type),
    CHECK (type IN ('usb', 'vm', 'sd')),
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production')),
    CHECK (downloadable_to IN ('anyone', 'student', 'teacher', 'nobody'))
);
-- Removed 2020-09-11
-- Don't see what is the purpose of this constraint anymore...
--     CHECK ((type = 'vm' AND host_architecture IS NULL) OR (type != 'vm' AND host_architecture IS NOT NULL)),

-- EOF
