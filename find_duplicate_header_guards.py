#!/usr/bin/env python3

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


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


@dataclass
class HeaderGuardStatus:
    ifndef_name: Optional[str] = None
    def_name: Optional[str] = None

    def get_error(self) -> Optional[str]:
        if self.ifndef_name is None:
            return "'#ifndef' is missing"
        if self.def_name != self.ifndef_name:
            return f"#ifndef ('{self.ifndef_name}') != def_name('{self.def_name}')"
        return None


def get_header_guard_status(data: str) -> Optional[HeaderGuardStatus]:
    # https://regex101.com/r/KKcUWF/2
    re_header_guard_name = re.compile(r"#ifndef (\w+)\s?.*\n#define")
    header_guard_tag = re.search(re_header_guard_name, data)
    if not header_guard_tag:
        return None
    header_guard_tag = header_guard_tag.group(1)
    return HeaderGuardStatus(
        header_guard_tag,  # ifndef_name
        header_guard_tag,  # def_name
    )


def uses_pragma_once(data: str) -> bool:
    # https://regex101.com/r/yBPzdj/2
    re_pragma_once = re.compile(r"^#pragma once\s?\n")
    pragma_once = re.match(re_pragma_once, data)
    return True if pragma_once else False


@dataclass
class HeaderStatus:
    file_path: str
    header_guard_status: Optional[HeaderGuardStatus] = None
    uses_pragma_once: bool = False


def check_header(file_path: str) -> HeaderStatus:
    with open(file_path, "r", errors="ignore") as file:
        data = file.read()

    if uses_pragma_once(data):
        return HeaderStatus(
            file_path,  # file_path
            None,  # header_guard_status
            True,  # uses_pragma_once
        )
    status = get_header_guard_status(data)
    if status:
        return HeaderStatus(
            file_path,  # file_path
            status,  # header_guard_status
            False,  # uses_pragma_once
        )

    return HeaderStatus(
        file_path,  # file_path
        None,  # header_guard_status
        False,  # uses_pragma_once
    )


def map_guard_tag_to_filepaths(statuses: List[HeaderStatus]) -> Dict[str, List[str]]:
    ret: Dict[str, List[str]] = {}

    for status in statuses:
        if not status.header_guard_status:
            raise ValueError(f"{status} does not have a header_guard_status")
        if not status.header_guard_status.ifndef_name:
            raise ValueError(f"{status} does not have a ifndef tag")
        tag = status.header_guard_status.ifndef_name
        if tag not in ret:
            ret[tag] = []

        ret[tag].append(status.file_path)

    return ret


def main():
    ignore_dirs = dirs_to_ignore()
    sub_dirs = get_sub_dirs_to_search(os.getcwd(), ignore_dirs)
    headers: List[str] = []
    for dir in sub_dirs:
        headers.extend(find_header_files(dir))
    print(f"Number of header files found: {len(headers)}")

    header_statuses: List[HeaderStatus] = []
    for header in headers:
        header_statuses.append(check_header(header))

    print(f"Number of header files processed: {len(header_statuses)}")

    no_header_duplication_protection = [
        s
        for s in header_statuses
        if not s.header_guard_status and not s.uses_pragma_once
    ]
    print(
        f"Number of header files without protection: {len(no_header_duplication_protection)}"
    )

    for status in no_header_duplication_protection:
        print(f"\t{status.file_path}")

    include_guards = [s for s in header_statuses if s.header_guard_status]

    guard_tags_to_filepaths = map_guard_tag_to_filepaths(include_guards)

    repeated_tags = [
        (tag, paths) for tag, paths in guard_tags_to_filepaths.items() if len(paths) > 1
    ]

    print(f"Number of files using header guards: {len(include_guards)}")
    print(f"Number of unique header guards: {len(guard_tags_to_filepaths)}")
    print(f"Number of header guards that have been resued: {len(repeated_tags)}")

    for tag, files in repeated_tags:
        print(f"TAG: {tag}")
        for file in files:
            print(f"\t{file}")


if __name__ == "__main__":
    main()
