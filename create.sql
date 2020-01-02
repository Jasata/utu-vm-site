CREATE TABLE teacher
(
    uid             TEXT        NOT NULL PRIMARY KEY,
    created         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          TEXT        NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'inactive'))
);
CREATE TABLE file
(
    id              INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name            TEXT        NOT NULL UNIQUE,
    size            INTEGER     NOT NULL,
    sha1            TEXT            NULL,
    type            TEXT        NOT NULL,
    label           TEXT        NOT NULL,
    version         TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now')),
    ostype          TEXT            NULL,
    description     TEXT            NULL,
    ram             TEXT            NULL,
    cores           TEXT            NULL,
    disksize        TEXT            NULL,
    dtap            TEXT        NOT NULL DEFAULT 'production',
    created         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    owner           TEXT        NOT NULL,
    downloadable_to TEXT        NOT NULL DEFAULT 'nobody',
    FOREIGN KEY (owner) REFERENCES teacher (uid),
    UNIQUE(label, version, type),
    CHECK (type IN ('usb', 'vm')),
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production')),
    CHECK (downloadable_to IN ('anyone', 'student', 'teacher', 'nobody'))
);
CREATE TABLE uses
(
    uid             TEXT        NOT NULL,
    id              INTEGER     NOT NULL,
    PRIMARY KEY (uid, id),
    FOREIGN KEY (uid) REFERENCES teacher (uid),
    FOREIGN KEY (id)  REFERENCES file (id) ON DELETE CASCADE
);
