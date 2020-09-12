-- create.sql - SQLite3 creation script for vm.utu.fi site
--
-- 2020-09-10   Add 'upload' table (STILL UNUSED!).
-- 2020-09-11   Removed type and host_architecture CHECK constraint from 'file'
--
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
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production')),
    CHECK (downloadable_to IN ('anyone', 'student', 'teacher', 'nobody'))
);
-- Don't see what is the purpose of this constraint anymore...
--     CHECK ((type = 'vm' AND host_architecture IS NULL) OR (type != 'vm' AND host_architecture IS NOT NULL)),
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
CREATE TABLE downloadable
(
    filename            TEXT        NOT NULL,
    file_id             INTEGER         NULL,
    size                INTEGER     NOT NULL,
    created             TIMESTAMP   NOT NULL DEFAULT (strftime('%s', 'now')),
    deleted             TIMESTAMP       NULL,
    PRIMARY KEY (filename, created),
    CHECK (deleted IS NULL OR (deleted > created)),
    FOREIGN KEY (file_id) REFERENCES file (id) ON DELETE SET NULL
);
CREATE TABLE download
(
    datetime            TIMESTAMP   NOT NULL,
    filename            TEXT        NOT NULL,
    size                INTEGER     NOT NULL,
    complete            TEXT            NULL,
    file_id             INTEGER         NULL,
    CHECK (complete IS NULL OR complete IN ('TRUE', 'FALSE'))
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

-- Ideal solution would have been Nginx logging, storing full/partial status.
-- Such information is apparently not available from Nginx logging.
--
-- file -table data will NOT be permanent. There is enough name collisions to
-- come even without accumulating filenames that no longer exist.
-- => file -table data WILL be deleted when the file is removed.
--
-- This also means that there eventually will be log entries for filename(s)
-- that do not refer to the same actual image.
-- However, a two files cannot exist with the same filename at the same time.
-- This fact makes time another defining attribute.
-- Thus, download statistics will be for "a {file} that existed on {datetime}".
-- This in turn implies a journal of all images, but having such will also
-- re-enable full vs partial download determination.
--
-- 
CREATE TRIGGER IF NOT EXISTS file_ari
    AFTER INSERT
    ON file
BEGIN
    INSERT INTO downloadable (
        filename,
        file_id,
        size
    )
    VALUES (
        NEW.name,
        NEW.id,
        NEW.size
    );
END;
-- 
-- cascade foreign key actions do not activate triggers, thus:
CREATE TRIGGER IF NOT EXISTS file_ard
    AFTER DELETE
    ON file
BEGIN
    UPDATE  downloadable
    SET     deleted = strftime('%s', 'now')
    WHERE   file_id = OLD.id;
END;
-- Set download.complete column value
-- Compares bytes_sent to size of a file that existed when the log row was
-- written. TRUE if sizes are equal, FALSE if not and NULL if no file existed
-- when the download was logged.
CREATE TRIGGER IF NOT EXISTS download_ari
    AFTER INSERT
    ON download
BEGIN
    UPDATE  download
    SET     complete = (
                SELECT  CASE
                            WHEN d.size IS NULL THEN NULL
                            WHEN d.size - NEW.size = 0 THEN "TRUE"
                            ELSE "FALSE"
                        END AS completed
                FROM    (
                        SELECT      NEW.filename AS filename,
                                    NEW.size AS size
                        ) dl LEFT OUTER JOIN
                        (
                        SELECT      max(created) AS created,
                                    filename,
                                    size
                        FROM        downloadable
                        WHERE       created <= NEW.datetime
                                    AND
                                    (
                                        deleted IS NULL
                                        OR
                                        deleted >= NEW.datetime
                                    )
                                    AND
                                    filename = NEW.filename
                        GROUP BY    filename,
                                    size
                        ) d
                        ON
                        dl.filename = d.filename
            ),
            file_id = (
                SELECT  file_id
                FROM    (
                        SELECT      max(created) AS created,
                                    file_id
                        FROM        downloadable
                        WHERE       created <= NEW.datetime
                                    AND
                                    (
                                        deleted IS NULL
                                        OR
                                        deleted >= NEW.datetime
                                    )
                                    AND
                                    filename = NEW.filename
                        GROUP BY    file_id
                        )
            )
    WHERE   rowid = NEW.rowid;
END;
