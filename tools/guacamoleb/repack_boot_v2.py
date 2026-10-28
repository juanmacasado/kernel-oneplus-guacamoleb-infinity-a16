#!/usr/bin/env python3
"""Offline kernel-only repack of a pinned Android boot v2, unsigned AVB template.

Uses only Python's standard library. Never runs external tools or opens devices.
Formats: AOSP bootimg.h, mkbootimg.py and libavb/avbtool.py.
Signed AVB images are rejected; no verification flags or rollback values change.
"""

import argparse
import hashlib
import json
from pathlib import Path
import stat
import struct


def require(condition, message):
    if not condition:
        raise ValueError(message)


def align(size, boundary):
    return (size + boundary - 1) // boundary * boundary


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def image_id(sections):
    h = hashlib.sha1()
    for name in ['kernel', 'ramdisk', 'second', 'recovery_dtbo', 'dtb']:
        b = sections[name]
        h.update(b)
        h.update(struct.pack('<I', len(b)))
    return h.digest() + bytes(12)


def parse(data):
    require(len(data) >= 8192, 'truncated image')
    require(data[:8] == b'ANDROID!', 'not an Android boot image')
    u32 = lambda offset: struct.unpack_from('<I', data, offset)[0]
    require(u32(40) == 2 and u32(1644) == 1660, 'requires boot header v2')
    page = u32(36)
    require(page == 4096, 'requires known 4096-byte page format')
    require((u32(44) >> 25) == 16, 'requires Android 16 template')
    sizes = [u32(8), u32(16), u32(24), u32(1632), u32(1648)]
    names = ['kernel', 'ramdisk', 'second', 'recovery_dtbo', 'dtb']
    sections, offsets = {}, {}
    pos = page
    for name, size in zip(names, sizes):
        require(pos + size <= len(data) - 64, 'section exceeds image')
        offsets[name] = pos
        sections[name] = data[pos:pos + size]
        require(not any(data[pos + size:align(pos + size, page)]), 'nonzero section padding')
        pos += align(size, page)
    require(all(sections[n] for n in ['kernel', 'ramdisk', 'dtb']), 'missing required section')
    require(struct.unpack_from('<Q', data, 1636)[0] == offsets['recovery_dtbo'], 'unexpected recovery DTBO offset')
    require(not any(data[1660:page]), 'nonzero header padding')
    require(image_id(sections) == data[576:608], 'invalid boot image SHA-1 ID')
    footer = struct.unpack('>4sIIQQQ28s', data[-64:])
    magic, major, minor, original_size, vbmeta_offset, vbmeta_size, reserved = footer
    require(magic == b'AVBf' and (major, minor) == (1, 0) and not any(reserved), 'unsupported AVB footer')
    require(original_size == pos and vbmeta_offset == pos, 'unexpected AVB placement')
    require(vbmeta_size >= 256 and pos + vbmeta_size <= len(data) - page, 'invalid vbmeta size')
    vbmeta = data[pos:pos + vbmeta_size]
    require(vbmeta[:4] == b'AVB0', 'invalid vbmeta magic')
    auth, aux = struct.unpack_from('>QQ', vbmeta, 12)
    algo = struct.unpack_from('>I', vbmeta, 28)[0]
    require(algo == 0 and auth == 0, 'signed AVB template is not supported')
    require(256 + aux == vbmeta_size, 'invalid AVB auxiliary size')
    require(not any(data[pos + vbmeta_size:-64]), 'unexpected nonzero trailer')
    # NONE must have no signature, authentication hash, public key or key metadata.
    require(all(struct.unpack_from('>Q', vbmeta, o)[0] == 0 for o in [40, 56, 72, 88]), 'unexpected AVB authentication/key data')
    desc_offset, desc_size = struct.unpack_from('>QQ', vbmeta, 96)
    start, end = 256 + desc_offset, 256 + desc_offset + desc_size
    require(256 <= start <= end <= len(vbmeta), 'invalid descriptor range')
    hashes = []
    cursor = start
    while cursor < end:
        require(cursor + 16 <= end, 'truncated descriptor header')
        tag, following = struct.unpack_from('>QQ', vbmeta, cursor)
        length = following + 16
        require(length % 8 == 0 and length >= 16 and cursor + length <= end, 'invalid descriptor length')
        if tag == 2:
            require(length >= 132, 'truncated hash descriptor')
            image_size = struct.unpack_from('>Q', vbmeta, cursor + 16)[0]
            algorithm = vbmeta[cursor + 24:cursor + 56].rstrip(b'\0')
            plen, slen, dlen, flags = struct.unpack_from('>IIII', vbmeta, cursor + 56)
            require(algorithm == b'sha256' and dlen == 32 and plen == 4 and slen == 32, 'unsupported hash descriptor')
            require(length == align(132 + plen + slen + dlen, 8), 'hash descriptor length mismatch')
            require(vbmeta[cursor + 132:cursor + 132 + plen] == b'boot' and flags == 0, 'requires A/B boot hash descriptor')
            require(image_size == original_size, 'hash image size mismatch')
            salt_start = cursor + 132 + plen
            salt = vbmeta[salt_start:salt_start + slen]
            digest_start = salt_start + slen
            require(hashlib.sha256(salt + data[:image_size]).digest() == vbmeta[digest_start:digest_start + dlen], 'AVB hash mismatch')
            hashes.append({'offset': cursor, 'digest_offset': digest_start, 'salt': salt})
        else:
            require(tag == 0, 'only property and boot hash descriptors supported')
        cursor += length
    require(cursor == end and len(hashes) == 1, 'requires exactly one boot hash descriptor')
    return {'page': page, 'sections': sections, 'offsets': offsets,
            'vbmeta': vbmeta, 'hash': hashes[0], 'original_size': original_size}


def repack(template, kernel, partition_size):
    require(len(template) == partition_size, 'template/partition size mismatch')
    require(8192 <= partition_size <= 128 * 1024 * 1024 and partition_size % 4096 == 0, 'unsupported partition size')
    require(64 <= len(kernel) <= 64 * 1024 * 1024 and kernel[56:60] == b'ARM\x64', 'invalid raw ARM64 Image')
    old = parse(template)
    sections = dict(old['sections'], kernel=kernel)
    header = bytearray(template[:old['page']])
    struct.pack_into('<I', header, 8, len(kernel))
    header[576:608] = image_id(sections)
    new_dtbo_offset = old['page'] + sum(align(len(sections[n]), old['page']) for n in ['kernel', 'ramdisk', 'second'])
    struct.pack_into('<Q', header, 1636, new_dtbo_offset)
    output = header
    for value in sections.values():
        output += value
        output += bytes(align(len(value), old['page']) - len(value))
    size = len(output)
    meta = bytearray(old['vbmeta'])
    desc = old['hash']
    struct.pack_into('>Q', meta, desc['offset'] + 16, size)
    meta[desc['digest_offset']:desc['digest_offset'] + 32] = hashlib.sha256(desc['salt'] + output).digest()
    require(size + align(len(meta), old['page']) + old['page'] <= partition_size, 'new image exceeds boot partition')
    output += meta
    output += bytes(partition_size - 64 - len(output))
    output += struct.pack('>4sIIQQQ28s', b'AVBf', 1, 0, size, size, len(meta), bytes(28))
    new = parse(output)
    require(new['sections']['kernel'] == kernel, 'kernel changed while packing')
    require(all(new['sections'][n] == b for n, b in old['sections'].items() if n != 'kernel'), 'non-kernel component changed')
    # Only size, ID and relocation of recovery DTBO may change in the header.
    h = bytearray(output[:old['page']])
    for a, b in [(8, 12), (576, 608), (1636, 1644)]:
        h[a:b] = template[a:b]
    require(h == template[:old['page']], 'unexpected header change')
    return bytes(output)


def self_test(template):
    old = parse(template)
    kernel = old['sections']['kernel']
    require(repack(template, kernel, len(template)) == template, 'template round-trip differs')
    cases = {}
    def rejected(name, image, replacement=kernel, size=len(template)):
        try:
            repack(image, replacement, size)
        except (ValueError, struct.error):
            cases[name] = True
        else:
            raise AssertionError(name + ' was accepted')
    for name, offset, value in [('bad_magic', 0, b'BROKEN!!'), ('bad_page', 36, struct.pack('<I', 2048)), ('bad_version', 40, struct.pack('<I', 3)), ('bad_image_id', 576, b'BAD!'), ('bad_footer', len(template)-64, b'NOPE')]:
        b = bytearray(template); b[offset:offset + len(value)] = value; rejected(name, bytes(b))
    rejected('invalid_kernel', template, b'bad kernel')
    rejected('partition_size_mismatch', template, size=len(template) + 4096)
    b = bytearray(template); meta_offset = old['original_size']
    struct.pack_into('>I', b, meta_offset + 28, 1); rejected('signed_avb', bytes(b))
    b = bytearray(template); b[meta_offset + old['hash']['digest_offset']] ^= 1; rejected('bad_avb_digest', bytes(b))
    print(json.dumps({'byte_identical_round_trip': True, 'negative_cases': cases}, indent=2))


def read_regular(path, maximum):
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), 'input must be regular file')
    require(path.stat().st_size <= maximum, 'input too large')
    return path.read_bytes()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--template-sha256', required=True)
    p.add_argument('--kernel', type=Path)
    p.add_argument('--kernel-sha256')
    p.add_argument('--partition-size', type=int)
    p.add_argument('--output', type=Path)
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    template = read_regular(args.template, 128 * 1024 * 1024)
    require(sha256(template) == args.template_sha256, 'template SHA-256 mismatch')
    if args.self_test:
        self_test(template)
        return
    require(all([args.kernel, args.kernel_sha256, args.partition_size, args.output]), 'missing packing arguments')
    kernel = read_regular(args.kernel, 64 * 1024 * 1024)
    require(sha256(kernel) == args.kernel_sha256, 'kernel SHA-256 mismatch')
    output = repack(template, kernel, args.partition_size)
    # Exclusive creation refuses to overwrite inputs, existing artifacts or devices.
    with args.output.open('xb') as f:
        f.write(output)
    parsed = parse(output)
    print(json.dumps({'sha256': sha256(output), 'size': len(output),
                      'template_sha256': sha256(template), 'kernel_sha256': sha256(kernel),
                      'avb_algorithm': 'NONE (preserved; no signature)',
                      'sections': {n: {'size': len(b), 'sha256': sha256(b)} for n, b in parsed['sections'].items()},
                      'non_kernel_sections_preserved': True}, indent=2))


if __name__ == '__main__':
    main()
