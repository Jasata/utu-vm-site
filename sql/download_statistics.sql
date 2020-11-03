--
-- download_statistics.sql - Structures for vm.utu.fi download statistics
--
-- 2020-09-26   Adapted from old 'create.sql'
--
--
-- Download statistics (automatic)
--
--      This script creates table structures necessary for collecting download
--      statistics for files that are transient, and which names can be reused
--      by later uploads.
--
--      A "shadow table" is maintained by AFTER INSERT and AFTER DELETE
--      triggers. This table ('downloadable') records the creation AND deletion
--      datetime, giving each instance of a filename a period in time when it
--      has existed.
--
--      Because the 'file' can be deleted, the 'size' and 'filename'
--      information is also duplicated for reporting purposes.
--
-- ----------------------------------------------------------------------------
--
-- Inserting download events (Nginx logfile processor script)
--
--      Nginx logfile processor is expected to INSERT only three columns:
--      (filename, datetime, size) to 'dlevent' -view. INSTEAD OF trigger
--      will query and generate other information and make the actual
--      INSERT into the 'download' table.
--
--      This approach is necessary in order to circumvent NOT NULL primary key
--      constraint on 'download' table.
--
--      WHY?
--      If NULL values would be allowed in the 'download.file_id' primary key,
--      eventually there would be orphaned rows with NULL primary key values.
--      We cannot have NOT NULL 'download.file_id' primary key column because
--      (unfortunately) BEFORE INSERT triggers do not allow modifying NEW
--      (to populate NEW.file_id), thus preventing a solution with table-only.
--
--      The 'dlevent' view receives an INSTEAD OF trigger which will generate:
--
--      * 'download.complete'
--          Value of 'size' is compared between 'NEW' and 'downloadable':
--          TRUE    if sizes are equal
--          FALSE   if sizes differ
--          NULL    if no file existed when the download was logged
--
--      * 'download.file_id'
--          Trigger will retrieve 'downloadable.file_id', *IF* event 'datetime'
--          criteria finds a 'NEW.filename' to have existed at that time.
--
--      An exception is naturally generated for NULL 'NEW.file_id' if event
--      'datetime' cannot find a valid 'downloadable' record... and processor
--      script must store the offending Nginx log row separately for admins to
--      review and resolve (or delete).
--
-- ----------------------------------------------------------------------------
--
-- Identifying file
--
--      Files are considered to be transient. They are created and deleted.
--      File by exact same name may be later created again. Only real guarantee
--      is provided by the filesystem - two files by the same name cannot exist
--      at the same time.
--
--      Files are identified by their exact filename AND time period when the
--      file existed. This information is stored in 'downloadables' and managed
--      by triggers 'file_ari' and 'file_ard'.
--
--      Identification clause is as follows:
--
--          downloadable.filename = NEW.filename
--          AND
--          (
--              downloadable.created <= NEW.datetime
--              AND
--              (
--                  downloadable.deleted IS NULL
--                  OR
--                  downloadable.deleted >= NEW.datetime
--              )
--          )
--
--
-- NOTE
--      SQLite supports *only* FOR EACH ROW triggers. This is omitted in the
--      create syntax, but is reflected in the standardized trigger naming.
--      For example:
--          dlevent_iri = 'dlevent' -table trigger INSTEAD OF ROW INSERT



--
-- 'file' entity
--
CREATE TABLE downloadable
(
    file_id             INTEGER         NULL,
    filename            TEXT        NOT NULL,
    size                INTEGER     NOT NULL,
    created             TIMESTAMP   NOT NULL DEFAULT (strftime('%s', 'now')),
    deleted             TIMESTAMP       NULL,
    PRIMARY KEY (file_id),
    CHECK (deleted IS NULL OR (deleted > created))
);

--
-- event / download action
-- There is not UNIQUE over 'file_id' and 'datetime' because it is entirely
-- possible that two downloads get logged as the same time.
--
CREATE TABLE download
(
    file_id             INTEGER     NOT NULL,
    filename            TEXT        NOT NULL,
    datetime            TIMESTAMP   NOT NULL,
    size                INTEGER     NOT NULL,
    complete            TEXT            NULL,
    FOREIGN KEY (file_id) REFERENCES downloadable (file_id) ON DELETE CASCADE,
    CHECK (complete IS NULL OR complete IN ('TRUE', 'FALSE'))
);


--
-- Create 'downloadable' row after 'file' row has been inserted
--
CREATE TRIGGER IF NOT EXISTS file_ari
    AFTER INSERT
    ON file
BEGIN
    INSERT INTO downloadable (
        file_id,
        filename,
        size
    )
    VALUES (
        NEW.id,
        NEW.name,
        NEW.size
    );
END;

-- 
-- Record datetime of 'file' row delete
--
CREATE TRIGGER IF NOT EXISTS file_ard
    AFTER DELETE
    ON file
BEGIN
    UPDATE  downloadable
    SET     deleted = strftime('%s', 'now')
    WHERE   file_id = OLD.id;
END;

--
-- INSERT INTO dlevent -> INSERT INTO download
--
DROP VIEW IF EXISTS dlevent;
CREATE VIEW IF NOT EXISTS dlevent (filename, datetime, size)
AS SELECT NULL, NULL, NULL;

DROP TRIGGER IF EXISTS dlevent_iri;
CREATE TRIGGER IF NOT EXISTS dlevent_iri
    INSTEAD OF INSERT
    ON dlevent
BEGIN
    INSERT INTO download (file_id, filename, datetime, size, complete)
    SELECT      file_id,
                NEW.filename,
                NEW.datetime,
                NEW.size,
                CASE
                    WHEN d.size IS NULL THEN NULL
                    WHEN d.size - NEW.size = 0 THEN "TRUE"
                    ELSE "FALSE"
                END AS completed
    FROM        (
                    SELECT      NEW.filename AS filename,
                                NEW.size AS size
                ) dl LEFT OUTER JOIN
                (
                    SELECT      max(created) AS created,
                                file_id,
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
                    GROUP BY    file_id,
                                filename,
                                size
                ) d
                ON
                dl.filename = d.filename;
END;

-- EOF
