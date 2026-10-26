#!/usr/bin/env python3
"""Build data-shapes-contrib from the case table below, cross-checking every expectation.

    python3 bin/build.py            write tests/ and its manifests
    python3 bin/build.py --check    write nothing; fail if a file would change

Every case is one SHACL test file in the W3C layout (data-shapes-array's data-shapes-test-suite):
the shapes and the data in the file itself, an sht:Validate entry, and the expected validation report.
The expectation is jena-array's report (jena-shacl reads SHACL-array: a SHACL list is a sequence term,
and SHACL 1.2's list constraints apply to sequence values); a case whose shapes graph is ill-formed
under SHACL-array expects sht:Failure. rudof-array must give the same results (focus node, path,
severity, component, source shape, and the value where it reports one) for every case whose features
it has; it has no SHACL 1.2 list constraints yet, so those cases (mf:requires ra:ShaclListConstraints)
have jena-array alone. Implementations are found beside this checkout (../rdf-array/.tools with
jena-array's classpath, ../jena-array/jena-shacl, ../rudof-array/target/debug/rudof) or through
JENA_ARRAY_TOOL, JENA_SHACL_CLASSES and RUDOF.
"""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT.parent / 'rdf-array' / 'tools'
sys.path.insert(0, str(TOOLS))
import rdfarray as ra  # noqa: E402

JT = pathlib.Path(os.environ.get('JENA_ARRAY_TOOL', ROOT.parent / 'rdf-array' / '.tools'))
SHACL_CLASSES = os.environ.get('JENA_SHACL_CLASSES', str(ROOT.parent / 'jena-array' / 'jena-shacl' / 'target' / 'classes'))
RUDOF = os.environ.get('RUDOF', str(ROOT.parent / 'rudof-array' / 'target' / 'debug' / 'rudof'))
JAVA = os.environ.get('JAVA', '/opt/homebrew/opt/openjdk@21/bin/java')
CHECK = '--check' in sys.argv
SH = 'http://www.w3.org/ns/shacl#'
RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
EX = 'http://example/'
JS = 'jena-array jena-shacl src/test/files/local/rdf-array'
LIST = 'ra:ShaclListConstraints'

PREFIXES = '''PREFIX ex: <http://example/>
PREFIX mf: <http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#>
PREFIX ra: <https://rdf-array.github.io/rdf-array/vocab#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX sht: <http://www.w3.org/ns/shacl-test#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
'''

# ---------- directory, name, label, shapes and data (Turtle-array), requires, duplicates ----------
CASES = [
    # lists in the shapes graph
    ('path', 'seq-path-001', 'a sequence path is a sequence term', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:c ; sh:property ex:S-p .
ex:S-p sh:path ( ex:p ex:q ) ; sh:datatype xsd:string .
ex:a ex:p ex:b . ex:b ex:q "fine" .
ex:c ex:p ex:d . ex:d ex:q 1 .
''', [], [f'{JS}/seq-path-001.ttl']),
    ('path', 'seq-path-alternative-nested-001', 'an alternative path whose second member is a sequence path', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a ; sh:property ex:S-p .
ex:S-p sh:path [ sh:alternativePath ( ex:p ( ex:q ex:r ) ) ] ; sh:class ex:C .
ex:a ex:p ex:b ; ex:q ex:c . ex:c ex:r ex:d .
ex:b a ex:C .
''', [], []),
    ('path', 'nil-predicate-path-001', 'rdf:nil is an IRI, so sh:path rdf:nil is a predicate path, not an empty sequence path', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:b ; sh:property ex:S-p .
ex:S-p sh:path rdf:nil ; sh:minCount 1 .
ex:a rdf:nil 1 .
''', [], []),
    ('path', 'ladder-path-001', 'a path written as an rdf:first/rdf:rest ladder of blank nodes is not a sequence path, and a blank node with no path property is no path: the shapes graph is ill-formed', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a ; sh:property ex:S-p .
ex:S-p sh:path [ rdf:first ex:p ; rdf:rest ( ex:q ) ] ; sh:minCount 1 .
''', [], []),
    ('path', 'ladder-path-002', 'an IRI written as the head of an rdf:first/rdf:rest ladder is, as a path, the predicate path of that IRI', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a ; sh:property ex:S-p .
ex:S-p sh:path ex:l1 ; sh:minCount 1 .
ex:l1 rdf:first ex:p ; rdf:rest ( ex:q ) .
ex:a ex:p ex:b . ex:b ex:q ex:c .
''', [], []),
    ('path', 'empty-path-001', 'sh:path () is an empty sequence path: the shapes graph is ill-formed', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a ; sh:property ex:S-p .
ex:S-p sh:path () ; sh:minCount 1 .
''', [], []),
    ('node', 'seq-in-or-001', 'sh:in, sh:or and sh:not take sequence terms', '''
ex:S a sh:NodeShape ;
  sh:targetNode 1, 3, "x", true ;
  sh:or ( ex:InShape ex:StringShape ) ;
  sh:not ex:ThreeShape .
ex:InShape a sh:NodeShape ; sh:in ( 1 2 3 ) .
ex:StringShape a sh:NodeShape ; sh:datatype xsd:string .
ex:ThreeShape a sh:NodeShape ; sh:in ( 3 ) .
''', [], [f'{JS}/seq-in-or-001.ttl']),
    ('node', 'seq-languageIn-001', 'sh:languageIn takes a sequence term', '''
ex:S a sh:NodeShape ; sh:targetNode "a"@en, "b"@fr, "c"@de ; sh:languageIn ( "en" "fr" ) .
''', [], []),
    ('node', 'seq-closed-ignored-001', 'sh:ignoredProperties takes a sequence term', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:b ; sh:closed true ;
  sh:ignoredProperties ( rdf:type ) ;
  sh:property ex:S-p .
ex:S-p sh:path ex:p .
ex:a a ex:C ; ex:p 1 .
ex:b ex:p 1 ; ex:q 2 .
''', [], []),
    ('node', 'ladder-in-001', 'sh:in written as an rdf:first/rdf:rest ladder is not a list: the shapes graph is ill-formed', '''
ex:S a sh:NodeShape ; sh:targetNode 1 ; sh:in ex:l1 .
ex:l1 rdf:first 1 ; rdf:rest rdf:nil .
''', [], []),
    ('node', 'in-empty-001', 'sh:in () is the empty list; a warning shape with sh:minListLength 1 reports it (counterpart of SHACL 1.2 in-003)', '''
ex:TestInUnsatisfiableShape a sh:NodeShape ; sh:in () .
ex:InSubjectsShape a sh:NodeShape ; sh:targetSubjectsOf sh:in ; sh:property ex:InSubjectsShape-in .
ex:InSubjectsShape-in a sh:PropertyShape ; sh:path sh:in ; sh:minListLength 1 ; sh:severity sh:Warning .
''', [LIST], []),
    ('node', 'xone-empty-001', 'sh:xone () is the empty list; a warning shape with sh:minListLength 1 reports it (counterpart of SHACL 1.2 xone-003)', '''
ex:TestXoneUnsatisfiableShape a sh:NodeShape ; sh:targetClass ex:Person ; sh:xone () .
ex:XoneSubjectsShape a sh:NodeShape ; sh:targetSubjectsOf sh:xone ; sh:property ex:XoneSubjectsShape-xone .
ex:XoneSubjectsShape-xone a sh:PropertyShape ; sh:path sh:xone ; sh:minListLength 1 ; sh:severity sh:Warning .
''', [LIST], []),
    # sequence-valued data: SHACL 1.2's list constraints
    ('list', 'memberShape-property-001', 'sh:memberShape on the values of a property', '''
ex:IRIShape a sh:NodeShape ; sh:nodeKind sh:IRI .
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:b, ex:c, ex:d, ex:e ; sh:property ex:S-p .
ex:S-p sh:path ex:p ; sh:memberShape ex:IRIShape .
ex:a ex:p ( ex:x ex:y ) .
ex:b ex:p ( ex:x "s" ) .
ex:c ex:p ex:x .
ex:d ex:p () .
ex:e ex:p ex:l1 .
ex:l1 rdf:first ex:x ; rdf:rest rdf:nil .
''', [LIST], [f'{JS}/seq-member-shape-001.ttl']),
    ('list', 'memberShape-node-001', 'sh:memberShape on focus nodes that are sequences (counterpart of SHACL 1.2 node/memberShape-001)', '''
ex:IRIShape a sh:NodeShape ; sh:nodeKind sh:IRI .
ex:S a sh:NodeShape ; sh:targetObjectsOf ex:p ; sh:memberShape ex:IRIShape .
ex:a ex:p ( ex:x ex:y ) , ( ex:x "s" ) , () , ex:x , rdf:nil .
''', [LIST], []),
    ('list', 'listLength-property-001', 'sh:minListLength and sh:maxListLength on the values of a property', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:b, ex:c, ex:d ; sh:property ex:S-p .
ex:S-p sh:path ex:p ; sh:minListLength 1 ; sh:maxListLength 2 .
ex:a ex:p ( 1 ) .
ex:b ex:p () .
ex:c ex:p ( 1 2 3 ) .
ex:d ex:p rdf:nil .
''', [LIST], [f'{JS}/seq-list-length-001.ttl']),
    ('list', 'listLength-node-001', 'sh:minListLength and sh:maxListLength on focus nodes that are sequences (counterpart of SHACL 1.2 node/minListLength-001 and maxListLength-001)', '''
ex:S a sh:NodeShape ; sh:targetObjectsOf ex:p ; sh:minListLength 1 ; sh:maxListLength 2 .
ex:a ex:p ( 1 ) , () , ( 1 2 3 ) , ( ( 1 2 3 ) ) , ex:notAList .
''', [LIST], []),
    ('list', 'uniqueMembers-property-001', 'sh:uniqueMembers on the values of a property', '''
ex:S a sh:NodeShape ; sh:targetNode ex:a, ex:b, ex:c, ex:d ; sh:property ex:S-p .
ex:S-p sh:path ex:p ; sh:uniqueMembers true .
ex:a ex:p ( 1 2 ) .
ex:b ex:p ( 1 2 1 ) .
ex:c ex:p () .
ex:d ex:p ( ( 1 ) ( 1 ) ) .
''', [LIST], [f'{JS}/seq-unique-members-001.ttl']),
    ('list', 'uniqueMembers-node-001', 'sh:uniqueMembers on focus nodes that are sequences (counterpart of SHACL 1.2 node/uniqueMembers-001); 1 and "1" are different terms', '''
ex:S a sh:NodeShape ; sh:targetObjectsOf ex:p ; sh:uniqueMembers true .
ex:a ex:p ( 1 "1" ) , ( ex:x ex:x ) , ex:notAList .
''', [LIST], []),
    ('list', 'rgb-colour-001', 'an RGB colour: exactly three integers from 0 to 255 (shacl-array.md §2)', '''
ex:ColourShape a sh:NodeShape ; sh:targetClass ex:Swatch ; sh:property ex:ColourShape-rgb .
ex:ColourShape-rgb sh:path ex:rgb ; sh:minCount 1 ; sh:maxCount 1 ;
  sh:minListLength 3 ; sh:maxListLength 3 ; sh:memberShape ex:ByteShape .
ex:ByteShape a sh:NodeShape ; sh:datatype xsd:integer ; sh:minInclusive 0 ; sh:maxInclusive 255 .
ex:red a ex:Swatch ; ex:rgb ( 255 0 0 ) .
ex:pink a ex:Swatch ; ex:rgb ( 255 192 ) .
ex:blue a ex:Swatch ; ex:rgb ( 0 0 256 ) .
''', [LIST], []),
    ('list', 'polygon-001', 'a polygon: a sequence of points, each a sequence of two decimals (nested sequences as members)', '''
ex:PolygonShape a sh:NodeShape ; sh:targetObjectsOf ex:outline ; sh:minListLength 3 ; sh:memberShape ex:PointShape .
ex:PointShape a sh:NodeShape ; sh:minListLength 2 ; sh:maxListLength 2 ; sh:memberShape ex:DecimalShape .
ex:DecimalShape a sh:NodeShape ; sh:datatype xsd:decimal .
ex:triangle ex:outline ( ( 0.0 0.0 ) ( 1.0 0.0 ) ( 0.0 1.0 ) ) .
ex:line ex:outline ( ( 0.0 0.0 ) ( 1.0 1.0 ) ) .
ex:bent ex:outline ( ( 0.0 0.0 ) ( 1.0 ) ( 0.0 1.0 ) ) .
''', [LIST], []),
    ('list', 'playlist-001', 'a playlist: at least one track, no track twice, each track a ex:Track with a title (shacl-array.md §2)', '''
ex:PlaylistShape a sh:NodeShape ; sh:targetClass ex:Playlist ; sh:property ex:PlaylistShape-tracks .
ex:PlaylistShape-tracks sh:path ex:tracks ; sh:minCount 1 ;
  sh:minListLength 1 ; sh:uniqueMembers true ; sh:memberShape ex:TrackShape .
ex:TrackShape a sh:NodeShape ; sh:class ex:Track ; sh:property ex:TrackShape-title .
ex:TrackShape-title sh:path ex:title ; sh:minCount 1 .
ex:t1 a ex:Track ; ex:title "One" .
ex:t2 a ex:Track ; ex:title "Two" .
ex:t3 a ex:Track .
ex:good a ex:Playlist ; ex:tracks ( ex:t1 ex:t2 ) .
ex:repeats a ex:Playlist ; ex:tracks ( ex:t1 ex:t2 ex:t1 ) .
ex:untitled a ex:Playlist ; ex:tracks ( ex:t1 ex:t3 ) .
ex:empty a ex:Playlist ; ex:tracks () .
''', [LIST], []),
]

# Where rudof-array is known to differ from the expectation; still run, and reported if it stops differing
RUDOF_KNOWN = {
    'empty-path-001': 'rudof-array accepts sh:path (), an empty sequence path',
    'seq-in-or-001': 'rudof-array also reports the results of the shapes inside sh:or as results of the focus node (not specific to sequences)',
}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def write(path, text):
    path = ROOT / path
    if path.exists() and path.read_text() == text:
        return False
    if CHECK:
        print(f'would change: {path.relative_to(ROOT)}')
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return True


def jena_classpath():
    cp = (JT / 'cp.txt').read_text().strip()
    return f'{JT}:{SHACL_CLASSES}:{cp}'


def jena(path):
    """jena-array's report as quads, or None when the shapes graph is ill-formed."""
    p = run([JAVA, '-cp', jena_classpath(), 'JenaArray', 'shacl', str(path), str(path)])
    if p.returncode != 0:
        raise SystemExit(f'jena-array failed on {path}:\n{p.stderr[-2000:]}')
    if p.stdout.startswith('error:'):
        return None
    return ra.parse(p.stdout)


def rudof(path):
    """rudof-array's report as quads, or None when it refuses the shapes graph."""
    p = run([RUDOF, 'shacl-validate', '-r', 'ntriples', str(path)], timeout=120)
    if p.returncode != 0 or 'ValidationReport' not in p.stdout:
        return None
    return ra.parse(p.stdout)


def results(quads):
    """The results of a report: (focus, path, severity, component, source shape, value) term strings."""
    by_subj = {}
    for s, p, o, _ in quads:
        by_subj.setdefault(s, []).append((p, o))

    def path_str(t):
        if t[0] == 'bnode':  # a blank-node path: [ sh:inversePath … ] and the like
            return '[ ' + ' ; '.join(f'{ra.term_str(p)} {path_str(o)}' for p, o in sorted(by_subj.get(t, []))) + ' ]'
        if t[0] == 'seq':
            return '( ' + ' '.join(path_str(e) for e in t[1]) + ' )' if t[1] else '()'
        return ra.term_str(t)

    rows = []
    for s, props in by_subj.items():
        d = {p[1]: o for p, o in props if p[0] == 'iri'}
        if d.get(RDF + 'type') != ('iri', SH + 'ValidationResult'):
            continue
        shape = d.get(SH + 'sourceShape')
        rows.append((
            ra.term_str(d[SH + 'focusNode']),
            path_str(d[SH + 'resultPath']) if SH + 'resultPath' in d else None,
            ra.term_str(d[SH + 'resultSeverity']),
            ra.term_str(d[SH + 'sourceConstraintComponent']),
            ra.term_str(shape) if shape and shape[0] == 'iri' else None,
            ra.term_str(d[SH + 'value']) if SH + 'value' in d else None,
        ))
    return sorted(rows, key=lambda r: tuple(x or '' for x in r))


def turtle(term_string):
    """A term string (N-Triples-array, or a bracketed path) as Turtle-array, abbreviating ex:, rdf:, sh:."""
    for ns, prefix in ((EX, 'ex:'), (RDF, 'rdf:'), (SH, 'sh:')):
        term_string = term_string.replace(f'<{ns}', f'<{prefix}')
    out, i = [], 0
    while i < len(term_string):  # <ex:x> -> ex:x
        if term_string[i] == '<' and term_string[i + 1:i + 4] in ('ex:', 'rdf', 'sh:'):
            j = term_string.index('>', i)
            out.append(term_string[i + 1:j])
            i = j + 1
        else:
            out.append(term_string[i])
            i += 1
    return ''.join(out)


def report_turtle(rows):
    if rows is None:
        return '  mf:result sht:Failure ;\n'
    lines = ['  mf:result [', '      rdf:type sh:ValidationReport ;',
             f'      sh:conforms "{"false" if rows else "true"}"^^xsd:boolean ;']
    for focus, path, severity, component, shape, value in rows:
        lines.append('      sh:result [')
        lines.append('          rdf:type sh:ValidationResult ;')
        lines.append(f'          sh:focusNode {turtle(focus)} ;')
        if path:
            lines.append(f'          sh:resultPath {turtle(path)} ;')
        lines.append(f'          sh:resultSeverity {turtle(severity)} ;')
        lines.append(f'          sh:sourceConstraintComponent {turtle(component)} ;')
        if shape:
            lines.append(f'          sh:sourceShape {turtle(shape)} ;')
        if value:
            lines.append(f'          sh:value {turtle(value)} ;')
        lines.append('        ] ;')
    lines.append('    ] ;')
    return '\n'.join(lines) + '\n'


def test_file(name, label, body, requires, rows):
    req = ''.join(f'  mf:requires {r} ;\n' for r in ['ra:Sequences', *requires])
    return f'''{PREFIXES}
# Generated by bin/build.py -- edit the case table there.
{body.strip()}

<>
  rdf:type mf:Manifest ;
  mf:entries ( <{name}> ) ;
.

<{name}>
  rdf:type sht:Validate ;
  rdfs:label "rdf-array: {label.replace('"', chr(92) + '"')}" ;
{req}  mf:action [
      sht:dataGraph <> ;
      sht:shapesGraph <> ;
    ] ;
{report_turtle(rows)}  mf:status sht:approved ;
.
'''


def manifest(label, includes):
    inc = ' ;\n'.join(f'  mf:include <{i}>' for i in includes)
    return f'''PREFIX mf: <http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

# Generated by bin/build.py -- edit the case table there.
<>
  rdf:type mf:Manifest ;
  rdfs:label "{label}" ;
{inc} ;
.
'''


def main():
    problems, changed, dups, dirs = [], False, [], {}
    scratch = ROOT / '.build'
    scratch.mkdir(exist_ok=True)
    for d, name, label, body, requires, dup in CASES:
        # the expectation is computed from the file as it will be, with a placeholder result
        draft = scratch / f'{name}.ttl'
        draft.write_text(test_file(name, label, body, requires, []))
        jq = jena(draft)
        jrows = None if jq is None else results(jq)
        if LIST not in requires:
            rq = rudof(draft)
            rrows = None if rq is None else results(rq)
            difference = None
            if (jrows is None) != (rrows is None):
                difference = f'jena-array {"refuses" if jrows is None else "validates"}, rudof-array {"refuses" if rrows is None else "validates"}'
            elif jrows is not None:
                def key(r, with_value):
                    return r[:5] + ((r[5],) if with_value else ())
                both = all(r[5] for r in rrows) and all(r[5] for r in jrows)
                if sorted(key(r, both) for r in jrows) != sorted(key(r, both) for r in rrows):
                    difference = f'jena-array and rudof-array differ:\n  jena  {jrows}\n  rudof {rrows}'
            if name in RUDOF_KNOWN:
                if difference is None:
                    problems.append(f'{name}: rudof-array no longer differs; remove it from RUDOF_KNOWN')
            elif difference:
                problems.append(f'{name}: {difference}')
        changed |= write(f'tests/core/{d}/{name}.ttl', test_file(name, label, body, requires, jrows))
        dirs.setdefault(d, []).append(f'{name}.ttl')
        if dup:
            dups.append({'test': f'tests/core/{d}/{name}', 'duplicates': dup})
    for d, files in dirs.items():
        changed |= write(f'tests/core/{d}/manifest.ttl', manifest(f'rdf-array SHACL-array contrib tests: core/{d}', files))
    changed |= write('tests/core/manifest.ttl', manifest('rdf-array SHACL-array contrib tests: core', [f'{d}/manifest.ttl' for d in dirs]))
    changed |= write('tests/manifest.ttl', manifest('rdf-array SHACL-array contrib tests', ['core/manifest.ttl']))
    changed |= write('duplicates.json', json.dumps({'suite': 'data-shapes-contrib', 'tests': dups}, indent=1) + '\n')
    for p in problems:
        print('PROBLEM', p)
    if problems or (CHECK and changed):
        sys.exit(1)


if __name__ == '__main__':
    main()
