import os
import re
import click


CLICK_COMMAND_PATTERN = '\@click\.command\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'
CLICK_GROUP_PATTERN = '\@click\.group\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'


def import_command_or_group_from_dotpath(base_group: click.core.Group, dotpath: str, import_name: str, verbose: bool= False) -> None:
    '''
    Attempt to import into environment and add command to base group
        base_group - click.core.Group - base click group to add commands
        dotpath - str - attempted path to import
        import_name - str - attempted click group or command name to import and set as new bg_command
        verbose - bool [default:False] - print verbose output
    '''
    try:
        exec_cmd = f'from {dotpath} import {import_name}; global base_group_command; base_group_command={import_name}'
        exec(exec_cmd, globals())
        bg_command = globals().get('base_group_command')
        base_group.add_command(bg_command)
        if verbose:
            print(f'Successfully loaded and added command: {import_name}')
    except Exception as err:    
        if verbose:
            print(f'Failed to load: {dotpath}, {import_name}, {err}')


def load_commands_from_path(base_group: click.core.Group, filepath:str, verbose: bool= False) -> None:
    '''
    Attempt to load click commands from a given path that follow the click_dynamics structure
        base_group - click.core.Group - base click group to add commands
        filepath - str - attempted path to find commands
        verbose - bool [default:False] - print verbose output
    '''
    plugin_group_path = os.path.join(filepath, 'groups')
    plugin_group_init_path = os.path.join(plugin_group_path, '__init__.py')
    if os.path.exists(plugin_group_init_path):
        with open(plugin_group_init_path, 'r') as fin:
            raw = fin.read()
            click_imports = re.findall(CLICK_GROUP_PATTERN, raw) + re.findall(CLICK_COMMAND_PATTERN, raw)
            for import_name in click_imports:
                dotpath = plugin_group_path.replace("/", ".")
                import_command_or_group_from_dotpath(base_group, dotpath, import_name, verbose=verbose)
                    

def load_commands_from_directory(base_group: click.core.Group, directory: str, verbose: bool= False) -> None:
    '''
    Attempt to load click commands from a given directory
        base_group - click.core.Group - base click group to add commands
        directory - str - attempted path to find commands
        verbose - bool [default:False] - print verbose output
    '''
    plugins = [
        os.path.join(directory, fp) 
        for fp in os.listdir(directory) 
        if os.path.isdir(os.path.join(directory, fp)) and '__pycache__' not in fp
    ]
    for plugin_path in plugins:
        load_commands_from_path(base_group, plugin_path, verbose=verbose)