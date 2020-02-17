import os
import re
import click

from typing import Tuple


CLICK_COMMAND_PATTERN = '\@click\.command\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'
CLICK_GROUP_PATTERN = '\@click\.group\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'


def get_directories_from_path(filepath: str) -> list:
    '''
    Return all directories found within the given directory
    '''
    return [ os.path.join(filepath, fp) for fp in os.listdir(filepath) 
        if os.path.isdir(os.path.join(filepath, fp)) and '__pycache__' not in fp
    ]


def get_click_imports_from_path(filepath: str) -> Tuple[str, list]:
    '''
    Return the base path and all found groups or commands imports
    '''
    base_path = os.path.join(filepath, 'groups')
    init_path = os.path.join(base_path, '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r') as fin:
            data = fin.read()
            return base_path, re.findall(CLICK_GROUP_PATTERN, data) + re.findall(CLICK_COMMAND_PATTERN, data)
    return base_path, []


def import_from(dotpath: str, name: str):
    '''
    Import module and return instance of given function name
        dotpath - str - the dotpath for the import
        name - str - the method to import from the dotpath
    '''
    module = __import__(dotpath, fromlist=[name])
    return getattr(module, name) or None


def import_command_or_group_from_dotpath(base_group: click.core.Group, dotpath: str, import_name: str, verbose: bool= False) -> None:
    '''
    Attempt to import into environment and add command to base group
        base_group - click.core.Group - base click group to add commands
        dotpath - str - attempted path to import
        import_name - str - attempted click group or command name to import and set as new bg_command
        verbose - bool [default:False] - print verbose output
    '''
    msg = ''
    try:
        bg_command = import_from(dotpath, import_name)
        assert bg_command
        base_group.add_command(bg_command)
        msg = f'Successfully loaded and added command: {import_name}'
    except AssertionError:
        msg = f'Failed to load: {dotpath}, {import_name}, failed to get attribute from module'
    except Exception as err:    
        msg = f'Failed to load: {dotpath}, {import_name}, {err}'
    if verbose and msg:
        print(msg)


def load_commands_from_path(base_group: click.core.Group, filepath:str, verbose: bool= False) -> None:
    '''
    Attempt to load click commands from a given path that follow the click_dynamics structure
        base_group - click.core.Group - base click group to add commands
        filepath - str - attempted path to find commands
        verbose - bool [default:False] - print verbose output
    '''
    base_click_import_path, click_imports = get_click_imports_from_path(filepath)
    for import_name in click_imports:
        dotpath = base_click_import_path.replace("/", ".")
        import_command_or_group_from_dotpath(base_group, dotpath, import_name, verbose=verbose)


def load_commands_from_directory(base_group: click.core.Group, directory: str, verbose: bool= False) -> None:
    '''
    Attempt to load click commands from a given directory
        base_group - click.core.Group - base click group to add commands
        directory - str - attempted path to find commands
        verbose - bool [default:False] - print verbose output
    '''
    click_group_and_command_paths = get_directories_from_path(directory)
    for group_command_path in click_group_and_command_paths:
        load_commands_from_path(base_group, group_command_path, verbose=verbose)