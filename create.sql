/* 2019-12-07 Jani Tammi <jasata@utu.fi> */
CREATE TABLE file
(
    id              INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    name            TEXT        NOT NULL UNIQUE,
    label           TEXT        NOT NULL,
    version         TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%d', 'now')),
    description     TEXT            NULL,
    courses         TEXT            NULL,
    sha1            TEXT            NULL,
    size            INTEGER     NOT NULL,
    type            TEXT        NOT NULL,
    ram             TEXT            NULL,
    cores           TEXT            NULL,
    disk            TEXT            NULL,
    dtap            TEXT        NOT NULL DEFAULT 'production',
    created         INTEGER     NOT NULL DEFAULT (strftime('%s', 'now')),
    UNIQUE(label, version, type),
    CHECK (type IN ('usb', 'vm')),
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production'))
)
INSERT INTO file (label, version, size, sha1, name, type)
VALUES
("Java (generic)", "356", "1996267520", "a889307a9da4bf4ff1e8bb1e77e0153ca4f0206f", "utuvm-java-356.ova", "vm"),
("Java (generic)", "408", "2002370560", "ef4f0a9c7aa836ff4a1de4114881da0022ecb88a", "utuvm-java-408.ova", "vm"),
("C/C++/Web/Mobile/Data Science/Declarative", "356", "1504153600", "54fbf17296d90cbda41eaa8322fc10690fd16ee3", "utuvm-minimega-356.ova", "vm"),
("C/C++/Web/Mobile/Data Science/Declarative", "408", "1516615680", "fc887ab1cd106ab183a5aab3f4af173531068bde", "utuvm-minimega-408.ova", "vm"),
("DTEK2041 Embedded Systems Programming", "2019-12-06", "917", "deadbeef", "dtek2041-2019-12-06.ova", "vm"),
("Java (generic)", "356", "2216374659", "9088b7c1a30a5d2e8abb92697199045832c169e9", "utuvm-java-356.zip", "usb"),
("Java (generic)", "408", "2227312991", "15f69b088cee258c983ded4b3929b747b47a9d8a", "utuvm-java-408.zip", "usb"),
("Java (generic)", "412", "2348158976", "b236dc44bd5ced29d128dcc7191b3d2930824d5c", "utuvm-java-412.img", "usb"),
("C/C++/Web/Mobile/Data Science/Declarative", "356", "1726122925", "bf37bdb37e7b15ed21ec170baa086d2792bb66fd", "utuvm-minimega-356.zip", "usb"),
("C/C++/Web/Mobile/Data Science/Declarative", "408", "1743321017", "e35d3e02d8fc0383716a7a53cbb9d067eed819df", "utuvm-minimega-408.zip", "usb"),
("DTEK2041 Embedded Systems Programming", "2019-12-06", "91137", "deadbeef", "dtek2041-2019-12-06.zip", "usb"),
("DTEK2042 Expanded Systems Programming", "2019-12-06", "91123127", "deadbeef", "dtek2042-2019-12-06.zip", "usb"),
("DTEK2043 Extended Systems Programming", "2019-12-06", "12312917", "deadbeef", "dtek2043-2019-12-06.zip", "usb"),
("DTEK2044 Embarrassed Systems Programming", "2019-12-06", "12312917", "deadbeef", "dtek2044-2019-12-06.zip", "usb"),
("DTEK2045 Emansipated Systems Programming", "2019-12-06", "4112321917", "deadbeef", "dtek2045-2019-12-06.zip", "usb"),
("DTEK2046 Eloquent Systems Programming", "2019-12-06", "9412117", "deadbeef", "dtek2046-2019-12-06.zip", "usb");
/*
CREATE TABLE course
(
    id              INTEGER     NOT NULL PRIMARY KEY AUTOINCREMENT,
    code            TEXT        NOT NULL UNIQUE,
    name            TEXT            NULL,
    description     TEXT            NULL,
    password        TEXT            NULL,
    created         INTEGER     NOT NULL DEFAULT (strftime('%s', 'now'))
)
CREATE TABLE course_file
(
    course_id       INTEGER     NOT NULL,
    file_id         INTEGER     NOT NULL,
    created         INTEGER     NOT NULL DEFAULT (strftime('%s', 'now')),
    PRIMARY KEY (course_id, file_id),
    FOREIGN KEY (course_id) REFERENCES course (id),
    FOREIGN KEY (file_id)   REFERENCES file (id)
)

INSERT INTO course (code, name, description)
VALUES
('DTEK2041','Embedded Systems Programming', NULL),
('BOGUS0001', 'Bogus Course', 'Testing');

INSERT INTO course_file (course_id, file_id)
VALUES
(1, 1), (1, 2), (2, 2), (2, 3), (2, 4);

*/