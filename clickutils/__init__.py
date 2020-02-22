import os
import re
import click
import traceback

from contextlib import redirect_stdout
from typing import Tuple, Callable
from multiprocessing import Process


CLICK_COMMAND_PATTERN = '\@click\.command\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'
CLICK_GROUP_PATTERN = '\@click\.group\(.*\)[\s\S]*?(?=\n.*?=|def (.*)\(\):)'
CLICK_ADD_COMMAND_PATTERN = '.*\.add_command\((.*), .*\)'


def get_directories_from_path(filepath: str) -> list:
    '''
    Return all directories found within the given directory
    '''
    return [
        os.path.join(root, d)
        for root, dirs, files in os.walk(filepath) 
        for d in dirs
        if '__pycache__' not in os.path.join(root, d) and 'groups' in d
    ]

def get_click_imports_from_path(filepath: str) -> Tuple[str, list]:
    '''
    Return the base path and all found groups or commands imports
    '''
    click_import_table = []
    if os.path.exists(filepath) and os.path.isdir(filepath):
        for fname in os.listdir(filepath):
            fpath = os.path.join(filepath, fname)
            if os.path.isfile(fpath) and '.py' in fname:
                with open(fpath, 'r') as fin:
                    data = fin.read()
                    if '__init__.py' in fname:
                        citpath = filepath
                    else:
                        citpath = fpath.replace('.py', '')
                    click_import_table.append([
                        citpath, 
                        re.findall(CLICK_GROUP_PATTERN, data) + re.findall(CLICK_COMMAND_PATTERN, data), 
                        re.findall(CLICK_ADD_COMMAND_PATTERN, data)
                    ])

    return click_import_table


def get_dotpath(filepath: str):
    dotpath = filepath.replace("/", ".")
    while True:
        if len(dotpath) > 0:
            if dotpath[0] == '.':
                dotpath = dotpath[1:]
            else:
                break
        else:
            break
    
    return dotpath


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


def load_commands_from_path(base_group: click.core.Group, filepath:str, verbose: bool= False, basedir: str= None) -> None:
    '''
    Attempt to load click commands from a given path that follow the click_dynamics structure
        base_group - click.core.Group - base click group to add commands
        filepath - str - attempted path to find commands
        verbose - bool [default:False] - print verbose output
    '''
    click_import_table = get_click_imports_from_path(filepath)
    click_import_list = []
    negations = set()

    for base_click_import_path, import_name_list, negate_list in click_import_table:
        if basedir:
            base_click_import_path = base_click_import_path.replace(basedir, '')
        dotpath = get_dotpath(base_click_import_path)
        for import_name in import_name_list:
            click_import_list.append([base_group, dotpath, import_name])
        negations.update(negate_list)
    
    for base_group, dotpath, import_name in click_import_list:
        if import_name not in negations:
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
        load_commands_from_path(
            base_group, 
            group_command_path, 
            verbose=verbose, 
            basedir='/'.join(directory.split('/')[:-1])
        )


class test_click_command(object):
    '''
        class for testing click commands and reporting their traceback's
    '''
    def __init__(self, cmd: click.core.Command, *args: list, ):
        self.ok = True
        self.cmd = cmd
        self.error = ''
        self.name = cmd.name
        self.args = args
    
    def _run_silent_command(self, opts_list: list):
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull):
                try:
                    self.cmd(opts_list)
                except Exception as err:
                    self.error = ''.join(traceback.format_exception(None, err, err.__traceback__))
                    self.ok = False

    def __call__(self, verbose: bool= False):
        arg_values = {c.name: a for a, c in zip(self.args, self.cmd.params)}
        args_needed = {c.name: c for c in self.cmd.params
                    if c.name not in arg_values}
        
        opts = {a.name: a for a in self.cmd.params if isinstance(a, click.Option)}
        # check positional arguments list
        for arg in (a for a in self.cmd.params if isinstance(a, click.Argument)):
            if arg.name not in arg_values:
                raise click.BadParameter(f'Missing required positional parameter {arg.name!r}')
        
        opts_list = sum([[o.opts[0], str(arg_values[n])] for n, o in opts.items()], [])

        if verbose:
            print(f'Invoking command: {self.name!r}')
        p = Process(target=self._run_silent_command, args=[opts_list, ])
        p.start()
        p.join()
        if p.exitcode > 0 and self.ok:
            self.error = f'exit code: {p.exitcode!r}'
            self.ok = False
        
        return self.ok

class click_loader(object):
    '''
    Dynamically load groups and commands from structured project dir
    project_dir
    |_click_group
        |__groups (recursively searched)
            |__ __init__.py
            |__ group2.py
    '''
    class group(click.core.Group):
        '''
        clickutils decorator for dynamically creating a new group of commands
        '''
        def __init__(self, filepath: str, name: str= None, verbose: bool= False):
            super().__init__(self)
            self.verbose = verbose
            self.name = name
            if os.path.exists(filepath):
                self.filepath = filepath
            else:
                raise TypeError(f'Argument must be a valid filepath. Given path: {filepath!r} was not valid')
        
        def __call__(self, fn: Callable, **kwargs):
            
            grp = click.Group(self.name, **kwargs)
            
            if self.filepath:
                if os.path.isfile(self.filepath):
                    load_commands_from_path(grp, self.filepath, verbose=self.verbose)
                if os.path.isdir(self.filepath):
                    load_commands_from_directory(grp, self.filepath, verbose=self.verbose)
            else:
                msg = f'Self is of type: {type(self).__name__!r} and not {f"click.Group"!r}.'
                msg += f'Please make sure decorator is above click decorators.'
                raise TypeError(msg)

            return grp