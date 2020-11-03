--
-- Changes and development ideas for 2021 release of vm.utu.fi
--

--
-- Structure to link teacher to a course
-- THIS IS PROBLEMATIC - more than one teacher...
--
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



-- Table to list on-going (chunked) uploads
--
-- (An active) teacher may have an ongoing upload for only one vm image
-- of the same filename at the time (UNIQUE(owner, filename)).
-- filename         Name as offered by the client
-- filesize         In bytes
-- chunksize        Size of an upload chunk in bytes.
--                  Decided when row is created and for obvious reasons,
--                  must not be modified, or upload integrity fails.
-- chunklist        Serialized Python list object containing as many elements
--                  as there are chunks (Math.Ceil(filesize/chunksize))
--                  Has only values True or False. True signified successfully
--                  received chunk and False not transferred (or error).
-- created          Simply a timestamp to help cleanup scripts to identify
--                  failed and stale uploads.
CREATE TABLE upload
(
    upid                INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    owner               TEXT        NOT NULL,
    filename            TEXT        NOT NULL,
    filesize            INTEGER     NOT NULL,
    chunksize           INTEGER     NOT NULL,
    chunklist           TEXT        NOT NULL,
    created             TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner) REFERENCES teacher (uid),
    UNIQUE (owner, filename)
);

CREATE TRIGGER IF NOT EXISTS upload_bru
    BEFORE UPDATE
    ON upload
    FOR EACH ROW
    WHEN (NEW.chunksize != OLD.chunksize)
BEGIN
    SELECT RAISE(ABORT, 'chunksize value must not be changed!');
END;

