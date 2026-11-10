#!/usr/bin/env python3
"""Slice file tool: get/put/clear/at fixed-size source slots (size: SLOT). See SKILL.md."""
import mmap
import os
import re
import sys

SLOT = 1024
PAD = b" "        # 0x20: pad byte, and every byte of an empty block
EDGE = b"\n"      # 0x0A: header (byte 0 of first block) and footer (last byte of last block)
empty_slot = PAD * SLOT

# ---- generic slot format ----

def load_index(path):
    return open(path).read().splitlines()


def save_index(path, names):
    open(path, "w").write("\n".join(names) + "\n")


def slots_of(names, name):
    n = len(names)
    i = 0
    while i < n:
        if names[i] == name:
            k = i + 1
            while k < n and names[k] == name:
                k += 1
            return i, k - i
        i += 1
    return -1, 0


def first_empty(names, need):
    n = len(names)
    i = 0
    while i < n:
        if names[i] != "":
            i += 1
            continue
        k = i + 1
        while k < n and names[k] == "":
            k += 1
        if k - i >= need:
            return i
        i = k
    return -1


def double_memory(names, mm):
    n = len(names)
    mm.resize(n * 2 * SLOT)
    mm[n * SLOT :] = PAD * (n * SLOT)   # bulk memset to 0x20
    names.extend([""] * n)


def pack(body):
    # header + body + pad + footer, filling whole blocks
    if isinstance(body, str):
        body = body.encode()
    if not body.endswith(b"\n"):
        body += b"\n"
    used = 1 + len(body) + 1
    cap = ((used + SLOT - 1) // SLOT) * SLOT
    return EDGE + body + PAD * (cap - used) + EDGE


def unpack(raw):
    # drop header and footer, then the pad
    return raw[1:-1].rstrip(PAD)


def pair_paths(path):
    """foo.slicefn -> (foo.slicefn, foo.sliceindex)."""
    if not path.endswith(".slicefn"):
        sys.stderr.write("not a slicefn file: %s\n" % path)
        sys.exit(1)
    return path, path[:-len(".slicefn")] + ".sliceindex"


# ---- per-extension validation (C is the only entry) ----

def check_body_c(name, body):
    # C-specific: simple-function dialect (name(, <=6 args, no float by value)
    text = body.decode() if isinstance(body, bytes) else body
    m = re.search(r"\b" + re.escape(name) + r"\s*\(([^)]*)\)", text)
    if not m:
        sys.stderr.write("%s: no signature\n" % name)
        sys.exit(1)
    args = [p.strip() for p in m.group(1).split(",") if p.strip()]
    if len(args) > 6:
        sys.stderr.write("%s: %d args\n" % (name, len(args)))
        sys.exit(1)
    for a in args:
        if not re.search(r"\bfloat\b", a):
            continue
        if re.search(r"\bfloat\s*\*", a):
            continue
        if re.search(r"\bfloat\s+[A-Za-z_][A-Za-z0-9_]*\s*\[", a):
            continue
        sys.stderr.write("%s: float by value: %s\n" % (name, a))
        sys.exit(1)


def validate(source, name, body):
    if RUFFC:
        check_body_c(name, body)


# ---- CLI ----

def usage():
    sys.stderr.write("usage: slicefn.py [--ruffc] <file.slicefn> get|put|clear <name>\n       slicefn.py <file.slicefn> at < offsets\n")
    sys.exit(1)


# --ruffc (default off): Ruff-C checks on put
RUFFC = "--ruffc" in sys.argv
sys.argv = [a for a in sys.argv if a != "--ruffc"]
if len(sys.argv) < 3:
    usage()
SOURCE, INDEX = pair_paths(sys.argv[1])
cmd = sys.argv[2]

if cmd == "at":
    name = ""
elif len(sys.argv) < 4:
    usage()
else:
    name = sys.argv[3]
have = os.path.exists(SOURCE), os.path.exists(INDEX)
if have != (True, True):
    if cmd != "put" or have != (False, False):
        sys.stderr.write("slice pair incomplete: %s %s\n" % (SOURCE, INDEX))
        sys.exit(1)
    # put on a missing pair creates it: one empty slot, grown by put as needed
    open(SOURCE, "wb").write(empty_slot)
    open(INDEX, "w").write("\n")
names = load_index(INDEX)
f = open(SOURCE, "r+b")
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_WRITE)
if len(names) * SLOT != len(mm):
    sys.stderr.write("slice size mismatch: index %d slots, file %d bytes (want %d)\n"
                     % (len(names), len(mm), len(names) * SLOT))
    sys.exit(1)
at, count = slots_of(names, name)
if cmd == "at":
    # stdin: each line starts with a byte offset (e.g. grep -bo "offset:match"); rest ignored
    out = []
    for line in sys.stdin.buffer.read().splitlines():
        m = re.match(rb"[0-9]+", line)
        if not m:
            sys.stderr.write("at: no leading byte offset: %r\n" % line)
            sys.exit(1)
        off = int(m.group())
        if off >= len(mm):
            sys.stderr.write("at: offset %d past end (%d bytes)\n" % (off, len(mm)))
            sys.exit(1)
        out.append(names[off // SLOT] + "\n")
    sys.stdout.write("".join(out))
elif cmd == "get":
    if at < 0:
        sys.exit(1)
    sys.stdout.buffer.write(unpack(mm[at * SLOT : (at + count) * SLOT]))
elif cmd == "put":
    body = sys.stdin.buffer.read()
    validate(SOURCE, name, body)
    before = list(names)
    packed = pack(body)
    need = len(packed) // SLOT
    if at >= 0:
        for k in range(count):
            names[at + k] = ""
    else:
        count = 0
        at = 0
    dest = first_empty(names, need)
    while dest < 0:
        double_memory(names, mm)
        dest = first_empty(names, need)
    for k in range(need):
        names[dest + k] = name
    if count:
        for k in range(count):
            mm[(at + k) * SLOT : (at + k + 1) * SLOT] = empty_slot
    mm[dest * SLOT : (dest + need) * SLOT] = packed
    mm.flush()
    save_index(INDEX, names)
    # index patch: =<total lines> on growth, -<line> <name> emptied, +<line> <name> filled
    out = []
    if len(names) != len(before):
        out.append("=%d\n" % len(names))
    for i in range(len(before)):
        if before[i] and before[i] != names[i]:
            out.append("-%d %s\n" % (i, before[i]))
    for i in range(len(names)):
        if names[i] and (i >= len(before) or before[i] != names[i]):
            out.append("+%d %s\n" % (i, names[i]))
    sys.stdout.write("".join(out))
elif cmd == "clear":
    if at < 0:
        sys.exit(1)
    for k in range(count):
        names[at + k] = ""
        mm[(at + k) * SLOT : (at + k + 1) * SLOT] = empty_slot
    mm.flush()
    save_index(INDEX, names)
    sys.stdout.write("".join("-%d %s\n" % (at + k, name) for k in range(count)))
else:
    usage()
mm.close()
f.close()
