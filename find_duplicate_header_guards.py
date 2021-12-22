#!/usr/bin/env python3

import os
from pathlib import Path
from typing import List, Set
import sys


def is_header(file_name: str) -> bool:
    header_extensions = set([".h", ".hpp", ".hxx"])
    file_extensions = set([x.lower() for x in Path(file_name).suffixes])
    return len(file_extensions.intersection(header_extensions)) != 0


def dirs_to_ignore(ignore_source_control_dirs: bool = True) -> Set[str]:
    if ignore_source_control_dirs:
        return set([".git", ".svn"])
    else:
        return set([])


# src: https://stackoverflow.com/a/40347279
def get_sub_dirs_to_search(current_dir: str, dirs_to_ignore: Set[str]) -> List[str]:
    subfolders = [
        f.path
        for f in os.scandir(current_dir)
        if f.is_dir() and f.name not in dirs_to_ignore
    ]
    for current_dir in list(subfolders):
        subfolders.extend(get_sub_dirs_to_search(current_dir, dirs_to_ignore))
    return subfolders


def find_header_files(dir_to_search: str) -> List[str]:
    return [
        f.path for f in os.scandir(dir_to_search) if f.is_file() and is_header(f.name)
    ]


def main():
    ignore_dirs = dirs_to_ignore()
    sub_dirs = get_sub_dirs_to_search(os.getcwd(), ignore_dirs)
    headers: List[str] = []
    for dir in sub_dirs:
        headers.extend(find_header_files(dir))
    print(headers)


if __name__ == "__main__":
    main()
