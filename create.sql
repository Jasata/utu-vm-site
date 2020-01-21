CREATE TABLE teacher
(
    uid                 TEXT        NOT NULL PRIMARY KEY,
    created             TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              TEXT        NOT NULL DEFAULT 'active',
    CHECK (status IN ('active', 'inactive'))
);
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
    CHECK ((type = 'vm' AND host_architecture IS NULL) OR (type != 'vm' AND host_architecture IS NOT NULL)),
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production')),
    CHECK (downloadable_to IN ('anyone', 'student', 'teacher', 'nobody'))
);
CREATE TABLE course
(
    code                TEXT        NOT NULL PRIMARY KEY,
    name                TEXT        NOT NULL UNIQUE,
    teacher             TEXT        NOT NULL,
    FOREIGN KEY (teacher) REFERENCES teacher (uid) ON DELETE CASCADE,
    CHECK (code = upper(code))
);
CREATE TABLE uses_for
(
    teacher             TEXT        NOT NULL,
    file_id             INTEGER     NOT NULL,
    course_code         TEXT        NOT NULL,
    PRIMARY KEY (teacher, file_id, course_code),
    FOREIGN KEY (teacher) REFERENCES teacher (uid) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES file (id),
    FOREIGN KEY (course_code) REFERENCES course (code) ON DELETE CASCADE
);
CREATE TABLE downloads
(
    datetime            TEXT        NOT NULL,
    filename            TEXT        NOT NULL,
    size                INTEGER     NOT NULL
);
