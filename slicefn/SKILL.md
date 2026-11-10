---
name: slicefn
description: >
  REQUIRED for accessing `*.slice*` files.
---

# slicefn Skill

  Named sets of functions, accessible without parsing the source language by using fixed-size contiguous blocks of bytes.

  Storage: file pair on disk
- **read-only** access to `<name>.sliceindex` - newline delimited list of functions
- **tool-only** access to `<name>.slicefn.<ext>` - do not put the whole file into your context; prefer `grep -bo` or slicefn.py operations

  Tool Command: slicefn.py [--ruffc] <filename> <operation>
- Filename: path to the `.slicefn.*`
- Operations:
  `get <function>` - output the function definition stripped of header, footer, and padding
  `clear <function>` - replace a function definition with empty blocks; prints patch style output for the index
  `put <function>` - clear a function definition, then add the stdin function definition; returns patch style output for the index, as it may change
  `at` - each stdin line starts with a byte offset; the rest is ignored. output is a function name per input line
- Ext: language of function definitions, suitable for direct submission to a compiler
- Halt on any non-zero return value
- **Confirm with the user before a put operation that would create a file**

## Padding

Functions are embedded into contiguous fixed-size binary blocks. Each block maps to a line of text in the `.sliceindex` file. A function name may repeat in the slice index file for each block consumed.

- ascii space (0x20) is the pad byte appended to fill the rest of a function's last storage block.
- byte 0 of a function's first block is always newline (0x0A)
- last byte of a function's last block is always newline (0x0A)
- an empty block is ascii space (0x20)

## Growth (implementation detail of `put`)

- `*.slicefn.*`: Growth doubles the binary blob, bulk memset to ascii space (0x20)
- `*.sliceindex`: Growth means the line count doubles, append newline bytes (0x0A)

## `.sliceindex` file

- Newline-delimited text, exactly one line per block. Line `i` is the function name in block `i`, or empty.
- A function's name is on each of its block lines and no other; the first of those lines is its start.

### Cache Guidelines

The `.sliceindex` may be cached:
- `at`: valid cache
- `get <function>`: valid cache
- `put <function>`: patch the cache using stdout
- `clear <function>`: patch the cache using stdout
- `.sliceindex` contains duplicates, use a set for unique names

Function definitions may be cached after `get` or updated on `put` and removed on `clear`.

### Patch Format

Put and clear may patch the `.sliceindex` file, allowing the cache to update:

Diff style output is processed as:
- index growth operation: `=<lines>`
- empty line/name operation: `-<line> <name>`
- set line/name operation: `+<line> <name>`
- outputs are ordered by operation `=` `-` `+`: growth, empty, then set
- lines are never removed
- no output with return code of zero implies no change to the index

## Search

Use your preferred pattern matching tool, for example:
`grep -bo <your_args> <file> | slicefn.py <file> at`

This returns one name per match, so duplicates are expected. An offset in an empty block returns an empty line. An offset past the end returns non-zero. A line with no leading offset returns non-zero.

## Ruff-C Validation (`put` only)

- use `slicefn.py --ruffc` when the project's AGENTS.md opts in
- a target not ending in `.slicefn.c` returns non-zero

Checks:
- body contains `<function>(`
- at most 6 arguments
- no `float` by value
- `float *` and `float` arrays are fine
