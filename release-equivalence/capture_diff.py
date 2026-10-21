"""Compare two corrected-page captures (app-patched.json) value by value.

Usage: python release-equivalence/capture_diff.py ARCHIVED.json V180.json OUT.json
Every number present at the same path in both captures is compared: exactly equal, or scaled difference
abs(a - b) / max(1, abs(a)). Keys present in only one capture and differing strings are counted by path.
"""
import json, sys
from collections import Counter


def walk(x, y, path, out):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) ^ set(y)):
            out['keys_only_in_one'][path + '.' + k] += 1
        for k in sorted(set(x) & set(y)):
            walk(x[k], y[k], path + '.' + k, out)
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for u, v in zip(x, y):
            walk(u, v, path + '[]', out)
    elif isinstance(x, (int, float)) and not isinstance(x, bool) and isinstance(y, (int, float)) and not isinstance(y, bool):
        out['numbers'] += 1
        if x == y:
            out['numbers_equal'] += 1
        else:
            d = abs(x - y) / max(1.0, abs(x))
            out['numbers_differing_by_path'][path] += 1
            out['max_scaled_difference_by_path'][path] = max(out['max_scaled_difference_by_path'].get(path, 0.0), d)
    elif x != y:
        out['other_differences_by_path'][path] += 1


def main():
    a = json.load(open(sys.argv[1], encoding='utf-8'))
    b = json.load(open(sys.argv[2], encoding='utf-8'))
    assert [r['id'] for r in a] == [r['id'] for r in b], 'configuration ids differ'
    out = dict(numbers=0, numbers_equal=0, numbers_differing_by_path=Counter(), max_scaled_difference_by_path={},
               keys_only_in_one=Counter(), other_differences_by_path=Counter())
    for x, y in zip(a, b):
        walk(x, y, '$[]', out)
    out['configurations'] = len(a)
    out['max_scaled_difference'] = max(out['max_scaled_difference_by_path'].values(), default=0.0)
    with open(sys.argv[3], 'w', encoding='utf-8', newline='\n') as f:
        json.dump({k: (dict(sorted(v.items())) if isinstance(v, dict) else v) for k, v in out.items()}, f, indent=2)
        f.write('\n')
    print(f"{out['configurations']} configurations; {out['numbers_equal']}/{out['numbers']} numbers exactly equal; "
          f"max scaled difference {out['max_scaled_difference']:.3g}")


if __name__ == '__main__':
    main()
