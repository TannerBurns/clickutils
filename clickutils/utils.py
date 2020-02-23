import re
import os

from typing import Callable, Union

CLICK_COMMAND_PATTERN = re.compile('\@click\.command\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)')
CLICK_GROUP_PATTERN = re.compile('\@click\.group\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)')
CLICK_ADD_COMMAND_PATTERN = re.compile('.*\.add_command\((.*), .*\)')


def get_directories_from_path(filepath: str, patterns: list= ['groups'], ignores: list= ['__pycache__']) -> list:
    """Method for retrieving subdirectories matching patterns and ignoring specific keywords
    
    Arguments:
        filepath {str} -- path string '/path/to/walk'
    
    Keyword Arguments:
        patterns {list} -- any directory containing pattern will be returned (default: {['groups']})
        ignores {list} -- any directory that does not contain any ignore strings (default: {['__pycache__']})
    
    Returns:
        list -- Returns all directories matching any given patterns and not containing any dirs to ignore
    """
    return [
        os.path.join(root, d) for root, dirs, files in os.walk(filepath) for d in dirs
        if all(i not in os.path.join(root, d) for i in ignores) and any(p in d for p in patterns)
    ]


def get_dotpath(filepath: str) -> str:
    """return the dotpath of a file, remove all beginning '.'
    
    Arguments:
        filepath {str} -- '/path/to/import' -> 'path.to.import
    
    Returns:
        str -- the given filepath in blob format
    """
    dotpath = filepath.replace("/", ".")
    while len(dotpath) > 0:
        if dotpath[0] == '.':
            dotpath = dotpath[1:]
        else:
            break
    return dotpath


def import_from(dotpath: str, name: str) -> Union[Callable, None]:
    """Import module and return instance of given function name
    
    Arguments:
        dotpath {str} -- the dotpath for the import
        name {str} -- the method name to import
    
    Returns:
        Callable -- method attribute of import
    """
    module = __import__(dotpath, fromlist=[name])
    return getattr(module, name) or None
