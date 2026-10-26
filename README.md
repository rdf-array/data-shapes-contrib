# data-shapes-contrib

Tests that every [SHACL-array](https://rdf-array.github.io/rdf-array/shacl-array.html) implementation can
share, but that no W3C suite contains because they test what rdf-array changes in SHACL: a SHACL list is a
sequence term `( … )`, an `rdf:first`/`rdf:rest` ladder is triples and not a list, `()` is the empty list,
and SHACL 1.2's `sh:memberShape`, `sh:minListLength`, `sh:maxListLength` and `sh:uniqueMembers` apply to
sequence values. It is laid out like the SHACL test suites of
[data-shapes-array](https://github.com/rdf-array/data-shapes-array), the rdf-array fork of w3c/data-shapes,
in the same manifest vocabulary (one `sht:Validate` test per file, its shapes and data in the file itself),
so a runner that walks one walks the other. Published at <https://rdf-array.github.io/data-shapes-contrib/>.

| Directory | Tests |
|---|---|
| [tests/core/path](tests/core/path/manifest.ttl) | sequence paths, nested in alternative paths; `rdf:nil` as a predicate path; a ladder or `()` as a path |
| [tests/core/node](tests/core/node/manifest.ttl) | `sh:in`, `sh:or`, `sh:not`, `sh:languageIn`, `sh:ignoredProperties` with sequences; a ladder as `sh:in`; `sh:in ()` and `sh:xone ()` (the counterparts of SHACL 1.2's `in-003` and `xone-003`) |
| [tests/core/list](tests/core/list/manifest.ttl) | the four list constraints on property values and on focus nodes that are sequences (the counterparts of SHACL 1.2's node-level list tests), an RGB colour, a polygon, a playlist |

`mf:requires` says what a test needs, in the [rdf-array test vocabulary](https://rdf-array.github.io/rdf-array/vocab/):
`ra:Sequences`, and `ra:ShaclListConstraints` for the SHACL 1.2 list constraints over sequences. A test whose
shapes graph is ill-formed under SHACL-array expects `sht:Failure`.

## How the expectations were made

[bin/build.py](bin/build.py) holds every case and writes every file; nothing here is edited by hand. Each
test's expected report is jena-array's (`jena-shacl`), and rudof-array must give the same results for every
test whose features it has; rudof-array has no SHACL 1.2 list constraints yet, so the
`ra:ShaclListConstraints` tests have jena-array alone. `python3 bin/build.py --check` rebuilds and fails if
anything would change. The build needs the implementations checked out beside this repository (see the
script's header). Where rudof-array is known to differ, the build still runs it and says when it stops
differing (`RUDOF_KNOWN`):

- `path/empty-path-001`: rudof-array accepts `sh:path ()`, an empty sequence path.
- `node/seq-in-or-001`: rudof-array also reports the results of the shapes inside `sh:or` as results of the
  focus node; this is not specific to sequences.

The tests were seeded from jena-array's own (`jena-shacl/src/test/files/local/rdf-array/`), which stay where
they are; [contrib-duplicates.md](https://github.com/rdf-array/rdf-array/blob/main/contrib-duplicates.md) in
rdf-array/rdf-array lists which test each one reproduces.
