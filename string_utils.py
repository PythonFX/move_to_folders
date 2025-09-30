import os
import re
import file_utils
from exceptions import MultipleVideoNumberMatch, NoVideoNumberMatch


def get_video_number(file_name_or_path):
    file_name = file_utils.filename(file_name_or_path).upper()
    return _extract_video_number_from_string(file_name)


def get_video_number_with_tags(file_name_or_path):
    file_name = file_utils.filename(file_name_or_path).upper()
    video_number = _extract_video_number_from_string(file_name)
    if '4K' in file_name:
        video_number += '-4K'
    if '-C' in file_name:
        video_number += '-C'
    return video_number


def _extract_video_number_from_string(text):
    """
    Extracts substrings matching:
    - Exactly 2 to 5 uppercase letters (A-Z)
    - Preceded by no other A-Z characters (no 6+ letters)
    - Followed by a hyphen (-)
    - Followed by exactly 3 digits
    - May be followed by other characters but not digits

    Returns a list of all matches found.
    """
    text = text.upper()
    pattern = r'(?<![A-Z])([A-Z]{2,5}-\d{3})(?![0-9])'
    result = re.findall(pattern, text)
    if len(result) == 1:
        return result[0]
    if len(result) == 0:
        pattern = pattern = r'(?<![A-Z])([A-Z]{2,5}-\d{4})(?![0-9])'
        result = re.findall(pattern, text)
        if len(result) == 1:
            return result[0]
        if len(result) == 0:
            raise NoVideoNumberMatch
    raise MultipleVideoNumberMatch
