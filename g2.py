#!/usr/bin/env python3

"""
G2 Programming Language - Modern, elegant, and powerful
Version 2.0

A systems programming language with Python-like ease and Rust-like safety
"""

import sys
from cli import main
sys.dont_write_bytecode = True
if __name__ == '__main__':
    sys.exit(main())