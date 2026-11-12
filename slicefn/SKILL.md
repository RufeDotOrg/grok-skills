---
name: slicefn
description: >
  REQUIRED for accessing `*.slice*` files.
---

# slicefn Skill

  Named sets of functions, accessible without parsing the source language by using fixed-size contiguous blocks of bytes.

  Storage: file pair on disk
- **read-only** access to `<name>.sliceindex` - newline delimited list of functions
- **tool-only** access to `<name>.slicefn` - do not put the whole file into your context; prefer `rg -boe <regex>` or slicefn.py operations

  Tool Command: slicefn [--ruffc] <filename> <operation>
- Runner: prefer `slicefn` on PATH. If `command -v slicefn` fails, run `python3 slicefn.py` from this folder with the same arguments.
- Filename: path to the `.slicefn`
- Operations:
  `get <function>` - output the function definition stripped of header, footer, and padding
  `clear <function>` - replace a function definition with empty blocks; prints patch style output for the index
  `put <function>` - clear a function definition, then add the stdin function definition; returns patch style output for the index, as it may change. The implementation may refuse to place a function by returning non-zero; that code should be out of the `.slicefn`.
  `at` - each stdin line starts with a byte offset; the rest is ignored. output is a function name per input line. An offset in an empty block returns an empty line; an offset past the end or a line with no leading offset returns non-zero
  `search <pattern>` - literal one-pass search of the mmap buffer: on a hit, write that function's definition (same as `get`) to stdout and resume at the next bucket after the function. Each matching function is emitted once. The consumer may grep stdout for surrounding lines. For regular expressions, prefer `rg` or `grep`, for example `rg -boe <regex> <.slicefn>`.
- `.slicefn` is the only suffix, regardless of language
- Halt on any non-zero return value
- **Confirm with the user before a put operation that would create a file**

## Padding

Functions are embedded into contiguous fixed-size binary blocks. Each block maps to a line of text in the `.sliceindex` file. A function name may repeat in the slice index file for each block consumed.

- ascii space (0x20) is the pad byte appended to fill the rest of a function's last storage block.
- byte 0 of a function's first block is always newline (0x0A)
- last byte of a function's last block is always newline (0x0A)
- an empty block is ascii space (0x20)

## Growth (implementation detail of `put`)

- `*.slicefn`: Growth doubles the binary blob, bulk memset to ascii space (0x20)
- `*.sliceindex`: Growth means the line count doubles, append newline bytes (0x0A)

## `.sliceindex` file

- Newline-delimited text, exactly one line per block. Line `i` is the function name in block `i`, or empty.
- A function's name is on each of its block lines and no other; the first of those lines is its start.

### Cache Guidelines

The `.sliceindex` may be cached:
- `at`: valid cache
- `get <function>`: valid cache
- `search <pattern>`: valid cache
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

`search <pattern>` is a literal byte search of the mmap buffer, in one pass. On a hit, the full unpacked definition is written to stdout (same as `get`) and the walk resumes at the next bucket after that function, so several hits in one function still emit it once. A hit in an empty bucket is skipped. No hits is a zero exit with empty stdout. The consumer may grep that stdout for surrounding lines, or use it as-is.

For regular expressions, prefer `rg` or `grep` on the `.slicefn`, for example `rg -boe <regex> <.slicefn>`. Leading byte offsets can be piped to `at`.

## Ruff-C Validation (`put` only)

- use `--ruffc` when the project's AGENTS.md opts in

Checks:
- body contains `<function>(`
- at most 6 arguments
- no `float` by value
- `float *` and `float` arrays are fine
