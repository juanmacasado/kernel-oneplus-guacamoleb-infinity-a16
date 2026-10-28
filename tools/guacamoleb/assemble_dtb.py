#!/usr/bin/env python3
"""Map each template FDT byte-for-byte to a baseline build, then replace by path."""
import argparse
import hashlib
import json
from pathlib import Path
from repack_boot_v2 import parse, read_regular, require, sha256, split_dtbs, validate_dtb_replacement


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--template-sha256', required=True)
    p.add_argument('--baseline-dts', type=Path, required=True)
    p.add_argument('--new-dts', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    template = read_regular(args.template, 128 * 1024 * 1024)
    require(sha256(template) == args.template_sha256, 'template SHA-256 mismatch')
    old_blob = parse(template)['sections']['dtb']
    baseline = {}
    for file in sorted(args.baseline_dts.glob('*/*.dtb')):
        data = read_regular(file, 2 * 1024 * 1024)
        baseline.setdefault(hashlib.sha256(data).digest(), []).append((file, data))
    output, mapping = bytearray(), []
    for old, before in split_dtbs(old_blob):
        choices = baseline.get(hashlib.sha256(old).digest(), [])
        choices = [file for file, data in choices if data == old]
        require(len(choices) == 1, 'template DTB must match exactly one baseline path')
        relative = choices[0].relative_to(args.baseline_dts)
        new = read_regular(args.new_dts / relative, 2 * 1024 * 1024)
        validate_dtb_replacement(old, new)
        after = split_dtbs(new)[0][1]
        delta = {k: {'old': before.get(k, b'').hex(), 'new': after.get(k, b'').hex()}
                 for k in sorted(before.keys() | after.keys()) if before.get(k) != after.get(k)}
        mapping.append({'path': str(relative), 'offset': len(output),
                        'old_sha256': sha256(old), 'new_sha256': sha256(new),
                        'property_delta': delta})
        output += new
    require(len(mapping) == 20, 'expected twenty guacamoleb-family DTBs')
    validate_dtb_replacement(old_blob, bytes(output))
    require(not args.output.exists() and not args.report.exists(), 'output already exists')
    with args.output.open('xb') as f:
        f.write(output)
    with args.report.open('x') as f:
        json.dump({'sha256': sha256(output), 'size': len(output), 'mapping': mapping}, f, indent=2)
        f.write('\n')
    print(json.dumps({'dtbs': len(mapping), 'bytes': len(output), 'sha256': sha256(output),
                      'baseline_byte_matches': True, 'identity_order_and_fstab_preserved': True}))


if __name__ == '__main__':
    main()
