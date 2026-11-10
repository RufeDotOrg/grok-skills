# grok-skills

Agent skills. Each top-level folder is one skill: a `SKILL.md` plus any script it runs.

## Install

Copy a skill folder into your agent's skills directory and put that folder on `PATH`.

## Skills

### slicefn

Named sets of functions stored in fixed-size blocks, so an agent can find, read and replace one function without parsing the source language or loading the whole file.

- a pair on disk: `<name>.slicefn.<ext>` holds the code, `<name>.sliceindex` names each block
- the code file is valid source: `#include` it in C, or load it as a module in Python
- search with any grep that prints byte offsets; slicefn maps offsets back to function names
- writes print a small patch so an agent can keep its cached index current

Examples: [C](examples/slicefn/c) and [Python](examples/slicefn/python). Run each folder's `demo.sh`.

## License

MIT
