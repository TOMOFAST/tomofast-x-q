# -*- coding: utf-8 -*-

# Resource object code
#
# Created by: The Resource Compiler for PyQt5 (Qt v5.15.2)
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore

qt_resource_data = b"\
\x00\x00\x01\x10\
\x89\
\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\
\x00\x00\x17\x00\x00\x00\x18\x08\x06\x00\x00\x00\x11\x7c\x66\x75\
\x00\x00\x00\x07\x74\x49\x4d\x45\x07\xe8\x04\x08\x07\x3a\x30\x00\
\xc8\x45\x30\x00\x00\x00\x09\x70\x48\x59\x73\x00\x00\x0a\xf0\x00\
\x00\x0a\xf0\x01\x42\xac\x34\x98\x00\x00\x00\xaf\x49\x44\x41\x54\
\x78\xda\x63\xfc\xff\xff\xbf\x23\x03\x03\x83\x32\x10\xc7\x03\xb1\
\x0d\x03\xe5\xe0\x08\x10\x2f\x04\xe2\xbb\x0c\x40\xc3\x53\x80\xf8\
\xf3\x7f\xea\x02\x90\x79\x29\x8c\x40\xe2\x30\x95\x5c\x8c\xe1\x03\
\x90\xe1\xff\x69\x60\x30\x08\x7c\xa3\xa5\xe1\x0c\x4c\xb4\x32\x78\
\x68\x1b\xce\x02\x67\x31\x62\x91\xfd\x8f\x45\x9c\x84\x18\x62\xc1\
\xd0\xc4\x88\xc5\x00\x32\xa3\x9c\xf2\x60\x61\x44\xa3\xb1\xba\x9c\
\x18\x03\xc8\x0e\x16\x7c\x00\xd9\x40\x74\x8b\x60\xf1\x82\xc5\x52\
\xe2\x0c\xc7\x65\x11\xcc\x32\x1c\x16\xd0\x34\x29\x8e\x66\xff\x51\
\xc3\x89\x06\x9f\x40\x86\x6f\xa0\x91\xe1\xfb\x40\x49\x51\x1f\xc8\
\x38\x00\xc4\x02\x54\x34\xf8\x03\x10\x3b\x80\x6a\x7f\x10\xd6\x07\
\xe2\xf5\x54\xaa\xf9\xd7\x43\xcd\x63\x00\x00\x0c\x76\xde\x5e\x24\
\x14\xd5\xcf\x00\x00\x00\x00\x49\x45\x4e\x44\xae\x42\x60\x82\
"

qt_resource_name = b"\
\x00\x07\
\x07\x3b\xe0\xb3\
\x00\x70\
\x00\x6c\x00\x75\x00\x67\x00\x69\x00\x6e\x00\x73\
\x00\x0a\
\x05\xc3\xc6\xe8\
\x00\x54\
\x00\x6f\x00\x6d\x00\x6f\x00\x66\x00\x61\x00\x73\x00\x74\x00\x5f\x00\x78\
\x00\x08\
\x0a\x61\x5a\xa7\
\x00\x69\
\x00\x63\x00\x6f\x00\x6e\x00\x2e\x00\x70\x00\x6e\x00\x67\
"

qt_resource_struct_v1 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x14\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\
\x00\x00\x00\x2e\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
"

qt_resource_struct_v2 = b"\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x02\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x14\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\
\x00\x00\x00\x00\x00\x00\x00\x00\
\x00\x00\x00\x2e\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\
\x00\x00\x01\x8e\xbb\x00\x14\xa9\
"

qt_version = [int(v) for v in QtCore.qVersion().split('.')]
if qt_version < [5, 8, 0]:
    rcc_version = 1
    qt_resource_struct = qt_resource_struct_v1
else:
    rcc_version = 2
    qt_resource_struct = qt_resource_struct_v2

def qInitResources():
    QtCore.qRegisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()
