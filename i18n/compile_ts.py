#!/usr/bin/env python3
"""
Compile all Tomofast_x_*.ts files to .qm.
Preferred: call lrelease.exe directly.
lrelease is available at:
  C:\\Qt\\Tools\\QtDesignStudio\\qt5_design_studio_reduced_version\\bin\\lrelease.exe
Run: lrelease Tomofast_x_*.ts
"""
import os
import struct
import defusedxml.etree.ElementTree as ET

# Qt .qm magic bytes (version 2.1)
QM_MAGIC = b'\x3c\xb8\x64\x18\xca\xef\x9c\x95\xcd\x21\x1c\xbf\x60\xa1\xbd\xdd'

# .qm section tags
HASHES_TAG = 0x42
MESSAGES_TAG = 0x69
CONTEXTS_TAG = 0x2f
DEPENDENCIES_TAG = 0x88


def _write_u8(v):
    return struct.pack('>B', v & 0xFF)


def _write_u32(v):
    return struct.pack('>I', v & 0xFFFFFFFF)


def _encode_string(s):
    """Encode a string as length-prefixed UTF-16BE."""
    if s is None:
        return struct.pack('>I', 0xFFFFFFFF)
    encoded = s.encode('utf-16-be')
    return struct.pack('>I', len(encoded) // 2) + encoded


def _encode_bytes(b):
    """Encode bytes as length-prefixed."""
    if b is None:
        return struct.pack('>I', 0xFFFFFFFF)
    return struct.pack('>I', len(b)) + b


def _hash_key(context, source, comment=''):
    """Compute Qt's hash for a message."""
    # Qt uses a simple hash: h = 5381; for each char: h = ((h << 5) + h) ^ c
    def djb2(s):
        h = 5381
        for c in s.encode('utf-16-be'):
            h = ((h << 5) + h) ^ c
            h &= 0xFFFFFFFF
        return h

    h = 0
    for part in (source, comment):
        h ^= djb2(part)
    return h & 0xFFFFFFFF


def compile_ts(ts_path, qm_path):
    tree = ET.parse(ts_path)
    root = tree.getroot()

    # Collect contexts
    contexts_data = b''
    hashes = []

    for context_elem in root.findall('context'):
        ctx_name_elem = context_elem.find('name')
        ctx_name = ctx_name_elem.text if ctx_name_elem is not None else ''

        messages_data = b''
        for msg_elem in context_elem.findall('message'):
            src_elem = msg_elem.find('source')
            trans_elem = msg_elem.find('translation')
            source = src_elem.text if src_elem is not None and src_elem.text else ''
            translation = trans_elem.text if trans_elem is not None and trans_elem.text else ''
            comment = ''

            # Build message binary
            # Tag 0x08 = SourceText16 (source as UTF-16), 0x09 = Translation16
            # Tag 0x06 = SourceText (Latin-1), 0x03 = Translation
            # Use tag 0x08/0x09 for Unicode
            msg = b''
            # Tag 0x09: Translation (UTF-16)
            t_enc = translation.encode('utf-16-be')
            msg += _write_u8(0x09) + _write_u32(len(t_enc) // 2)
            msg += t_enc
            # Tag 0x08: SourceText (UTF-16)
            s_enc = source.encode('utf-16-be')
            msg += _write_u8(0x08) + _write_u32(len(s_enc) // 2)
            msg += s_enc
            # Tag 0x02: End
            msg += _write_u8(0x02) + _write_u32(0)

            h = _hash_key(ctx_name, source, comment)
            offset = len(messages_data)
            hashes.append((h, offset))
            messages_data += msg

        # Context record: name + messages
        ctx_record = _encode_bytes(ctx_name.encode('utf-8'))
        ctx_record += _encode_bytes(messages_data)
        contexts_data += _encode_bytes(ctx_record)

    # Sort hashes
    hashes.sort(key=lambda x: x[0])
    hashes_data = b''.join(struct.pack('>II', h, off) for h, off in hashes)

    # Build .qm file
    qm = QM_MAGIC
    for tag, data in [(HASHES_TAG, hashes_data), (MESSAGES_TAG, b''), (CONTEXTS_TAG, contexts_data)]:
        qm += _write_u8(tag) + _write_u32(len(data)) + data

    with open(qm_path, 'wb') as f:
        f.write(qm)
    print(f"Compiled: {qm_path} ({len(qm)} bytes)")


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for ts_file in os.listdir(script_dir):
        if ts_file.startswith('Tomofast_x_') and ts_file.endswith('.ts'):
            ts_path = os.path.join(script_dir, ts_file)
            qm_path = ts_path.replace('.ts', '.qm')
            try:
                compile_ts(ts_path, qm_path)
            except Exception as e:
                print(f"ERROR compiling {ts_file}: {e}")
