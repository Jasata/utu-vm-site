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
    _owner          TEXT        NOT NULL,
    FOREIGN KEY (_owner) REFERENCES teacher (uid),
    UNIQUE(label, version, type),
    CHECK (type IN ('usb', 'vm')),
    CHECK (dtap IN ('development', 'testing', 'acceptance', 'production'))
);
CREATE TABLE teacher
(
    uid             TEXT        NOT NULL PRIMARY KEY,
    created         INTEGER     NOT NULL DEFAULT (strftime('%s', 'now')),
    status          TEXT        NOT NULL DEFAULT 'enabled',
    CHECK (status IN ('enabled', 'disabled'))
);
CREATE TABLE uses
(
    uid             TEXT        NOT NULL,
    id              INTEGER     NOT NULL,
    PRIMARY KEY (uid, id),
    FOREIGN KEY (uid) REFERENCES teacher (uid),
    FOREIGN KEY (id)  REFERENCES file (id) ON DELETE CASCADE
);
INSERT INTO teacher (uid)
VALUES
('jmjmak'),
('jasata'),
('tuisku'),
('apmake'),
('tianyl'),
('sjprau');
INSERT INTO file (label, version, size, sha1, name, type, _owner)
VALUES
("Java (generic)", "356", "1996267520", "a889307a9da4bf4ff1e8bb1e77e0153ca4f0206f", "utuvm-java-356.ova", "vm", "jmjmak"),
("Java (generic)", "408", "2002370560", "ef4f0a9c7aa836ff4a1de4114881da0022ecb88a", "utuvm-java-408.ova", "vm", "jmjmak"),
("C/C++/Web/Mobile/Data Science/Declarative", "356", "1504153600", "54fbf17296d90cbda41eaa8322fc10690fd16ee3", "utuvm-minimega-356.ova", "vm", "jmjmak"),
("C/C++/Web/Mobile/Data Science/Declarative", "408", "1516615680", "fc887ab1cd106ab183a5aab3f4af173531068bde", "utuvm-minimega-408.ova", "vm", "jmjmak"),
("DTEK2041 Embedded Systems Programming", "2019-12-06", "917", "deadbeef", "dtek2041-2019-12-06.ova", "vm", "jasata"),
("Java (generic)", "356", "2216374659", "9088b7c1a30a5d2e8abb92697199045832c169e9", "utuvm-java-356.zip", "usb", "jmjmak"),
("Java (generic)", "408", "2227312991", "15f69b088cee258c983ded4b3929b747b47a9d8a", "utuvm-java-408.zip", "usb", "jmjmak"),
("Java (generic)", "412", "2348158976", "b236dc44bd5ced29d128dcc7191b3d2930824d5c", "utuvm-java-412.img", "usb", "jmjmak"),
("C/C++/Web/Mobile/Data Science/Declarative", "356", "1726122925", "bf37bdb37e7b15ed21ec170baa086d2792bb66fd", "utuvm-minimega-356.zip", "usb", "jmjmak"),
("C/C++/Web/Mobile/Data Science/Declarative", "408", "1743321017", "e35d3e02d8fc0383716a7a53cbb9d067eed819df", "utuvm-minimega-408.zip", "usb", "jmjmak"),
("DTEK2041 Embedded Systems Programming", "2019-12-06", "91137", "deadbeef", "dtek2041-2019-12-06.zip", "usb", "jasata"),
("DTEK2042 Expanded Systems Programming", "2019-12-06", "91123127", "deadbeef", "dtek2042-2019-12-06.zip", "usb", "jasata"),
("DTEK2043 Extended Systems Programming", "2019-12-06", "12312917", "deadbeef", "dtek2043-2019-12-06.zip", "usb", "jasata"),
("DTEK2044 Embarrassed Systems Programming", "2019-12-06", "12312917", "deadbeef", "dtek2044-2019-12-06.zip", "usb", "jasata"),
("DTEK2045 Emansipated Systems Programming", "2019-12-06", "4112321917", "deadbeef", "dtek2045-2019-12-06.zip", "usb", "jasata"),
("DTEK2046 Eloquent Systems Programming", "2019-12-06", "9412117", "deadbeef", "dtek2046-2019-12-06.zip", "usb", "jasata");

