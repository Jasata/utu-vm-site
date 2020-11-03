




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

SELECT  CASE
            WHEN d.size IS NULL THEN NULL
            WHEN d.size - 1010101 = 0 THEN "TRUE"
            ELSE "FALSE"
        END AS completed
FROM    (
        SELECT      'PAYLOAD.zip' AS filename
        ) dl LEFT OUTER JOIN
        (
        SELECT      max(created) AS created,
                    filename,
                    size
        FROM        downloadable
        WHERE       created <= strftime('%s', 'now') -- 1601148100
                    AND
                    (
                        deleted IS NULL
                        OR
                        deleted >= strftime('%s', 'now') -- 1601148100
                    )
                    AND
                    filename = 'PAYLOAD.zip'
        GROUP BY    filename,
                    size
        ) d
        ON
        dl.filename = d.filename
;


SELECT  file_id
FROM    (
        SELECT      max(created) AS created,
                    file_id
        FROM        downloadable
        WHERE       created <= strftime('%s', 'now')
                    AND
                    (
                        deleted IS NULL
                        OR
                        deleted >= strftime('%s', 'now')
                    )
                    AND
                    filename = 'PAYLOAD.zip'
        GROUP BY    file_id
        )
;

INSERT INTO dlevent (filename, datetime, size) VALUES ('PAYLOAD.zip', strftime('%s', 'now'), 2132124312);

