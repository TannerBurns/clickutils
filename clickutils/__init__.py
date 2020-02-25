import re
import os
import click
import traceback

from typing import Callable
from contextlib import redirect_stdout
from multiprocessing import Process

from clickutils.utils import CLICK_GROUP_PATTERN, CLICK_COMMAND_PATTERN, CLICK_ADD_COMMAND_PATTERN
from clickutils.utils import CLICKVIEWSET_PATTERN, FOUNDVIEWSET_FORMAT_PATTERN
from clickutils.utils import get_dotpath, get_directories_from_path, import_from, convert_args_to_opts


class click_loader(object):
    """
    load groups and commands from structured project dir

    project_dir(recursively searched for .*/groups)
    |_ __init__.py
    |_ click_group
        |__ groups (files searched here for groups or commands)
            |__ __init__.py
            |__ group2.py (extra file that could contain extra groups and/or commands)
    """
    @staticmethod
    def load_commands_from_path(
        base_group: click.core.Group, filepath:str, basedir: str= None, verbose: bool= False) -> None:
        """Attempt to load click commands from a given path that follow the click_dynamics structure
        
        Arguments:
            base_group {click.core.Group} -- base click group to add commands
            filepath {str} -- attempted path to find commands
        
        Keyword Arguments:
            basedir {str} -- part of directory to remove for relative importing -
                                this is necessary if not using relative imports (default: {None})
            verbose {bool} -- print verbose output (default: {False})
        """
        click_import_list = []
        negations = set()
        
        for base_click_import_path, import_name_list, negate_list in click_loader.get_click_imports_from_path(filepath):
            if basedir:
                if 'site-packages' in basedir:
                    basedir = '/'.join(basedir.split('/')[:-1])
                base_click_import_path = base_click_import_path.replace(basedir, '')
            dotpath = get_dotpath(base_click_import_path)
            click_import_list.extend([[base_group, dotpath, import_name] for import_name in import_name_list])
            negations.update(negate_list)
        
        for base_group, dotpath, import_name in click_import_list:
            if import_name not in negations:
                click_loader.import_command_or_group_from_dotpath(base_group, dotpath, import_name, verbose=verbose)

    @staticmethod
    def load_commands_from_directory(base_group: click.core.Group, directory: str, verbose: bool= False) -> None:
        """Attempt to load click commands from a given directory
        
        Arguments:
            base_group {click.core.Group} -- base click group to add commands
            directory {str} -- attempted path to find commands
        
        Keyword Arguments:
            verbose {bool} -- print verbose output (default: {False})
        """
        click_group_and_command_paths = get_directories_from_path(directory)
        for group_command_path in click_group_and_command_paths:
            click_loader.load_commands_from_path(
                base_group, 
                group_command_path,
                basedir=directory,
                verbose=verbose
            )

    @staticmethod
    def get_click_imports_from_path(filepath: str) -> list:
        """[summary]
        
        Arguments:
            filepath {str} -- path string '/path/to/potential/click/groups'
        
        Returns:
            list -- Return the base path and all found groups or commands imports
        """
        click_import_table = []
        if os.path.exists(filepath) and os.path.isdir(filepath):
            for fname in os.listdir(filepath):
                fpath = os.path.join(filepath, fname)
                if os.path.isfile(fpath) and fname.endswith('.py'):
                    with open(fpath, 'r') as fin:
                        data = fin.read()
                        click_import_table.append([
                            filepath if '__init__.py' in fname else fpath.replace('.py', ''), 
                            CLICK_GROUP_PATTERN.findall(data) + CLICK_COMMAND_PATTERN.findall(data) +
                                [viewset_definition
                                 for named_viewset in CLICKVIEWSET_PATTERN.findall(data)
                                 for viewset_definition in re.findall(
                                    FOUNDVIEWSET_FORMAT_PATTERN.format(named_viewset), data)
                                 ],
                            CLICK_ADD_COMMAND_PATTERN.findall(data)
                        ])
        return click_import_table
    
    @staticmethod
    def import_command_or_group_from_dotpath(
        base_group: click.core.Group, dotpath: str, import_name: str, verbose: bool= False) -> None:
        """Attempt to import into environment and add command to base group
        
        Arguments:
            base_group {click.core.Group} -- base click group for adding commands
            dotpath {str} -- dotpath for potential click group or command
            import_name {str} -- method name for import
        
        Keyword Arguments:
            verbose {bool} -- print verbose output (default: {False})
        """
        msg = ''
        try:
            bg_command = import_from(dotpath, import_name)
            assert bg_command
            base_group.add_command(bg_command)
            msg = f'Successfully loaded and added command: {import_name}'
        except AssertionError:
            msg = f'Failed to load: {dotpath}, {import_name}, failed to get attribute from module'
        except Exception as err:
            tb = ''.join(traceback.format_exception(None, err, err.__traceback__))
            msg = f'Failed to load: {dotpath}, {import_name}, {tb}'
        if verbose and msg:
            print(msg)

    @staticmethod
    def load(base_group: click.core.Group, filepath: str, verbose: bool= False):
        """method for dynamically loading groups and commands from a filepath for file or dir
        
        Arguments:
            base_group {click.core.Group} -- base click group for adding commands
            filepath {str} -- filepath to attempt load
        
        Keyword Arguments:
            verbose {bool} -- print verbose output (default: {False})
        """
        if os.path.isfile(filepath):
            click_loader.load_commands_from_path(base_group, filepath, verbose=verbose)
        elif os.path.isdir(filepath):
            click_loader.load_commands_from_directory(base_group, filepath, verbose=verbose)
        else:
            if verbose:
                print(f'Filepath was not a valid file or directory')


    class group(object):
        """click_loader.group - extended click.group

        decorator for loading groups and commands from a structured click directory
        this decorator is equal to @click.group, if given a directory groups and commands will attempted
        to be found and imported into the click environment

        Keyword Arguments:
            filepath {str} -- filepath to load (default: {''})
            name {str} -- name of group (default: {''})
            verbose {bool} -- print verbose output (default: {False})
        """
        def __init__(self, filepath: str= '', name: str= '', verbose: bool= False):
            self.verbose = verbose
            self.name = name if name else None
            if os.path.exists(filepath):
                self.filepath = filepath
        
        def __call__(self, *args: list, **kwargs: dict):
            """when command is invoked
            
            Returns:
                click.Group -- new group with loaded groups and commands if filepath is found
            """
            grp = click.Group(self.name, **kwargs)
            
            if hasattr(self, 'filepath'):
                click_loader.load(grp, self.filepath, verbose=self.verbose)
                
            return grp



class test_click_command(object):
    """test_click_command

    class for testing click commands and capturing their traceback

    Arguments:
        cmd {click.core.Command} -- command to test
        args {list} -- list of positional args to map for click command
    """
    def __init__(self, cmd: click.core.Command, *args: list):
        self.ok = True
        self.cmd = cmd
        self.error = ''
        self.name = cmd.name
        self.args = args
    
    def _run_silent_command(self, opts_list: list):
        """run a command silently and redirect all stdout
        
        Arguments:
            opts_list {list} -- list of click options
        """
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull):
                try:
                    self.cmd(opts_list)
                except Exception as err:
                    self.error = ''.join(traceback.format_exception(None, err, err.__traceback__))
                    self.ok = False

    def __call__(self, verbose: bool= False) -> bool:
        """[summary]
        
        Keyword Arguments:
            verbose {bool} -- print verbose output (default: {False})
        
        Raises:
            click.BadParameter: a bad param was sent to the command being tested
        
        Returns:
            bool -- returns stats of ran command true == no errors, false == errors
        """
        opts_list = convert_args_to_opts(self.cmd, self.args)

        if verbose:
            print(f'Invoking command: {self.name!r}')
        p = Process(target=self._run_silent_command, args=[opts_list, ])
        p.start()
        p.join()
        if p.exitcode > 0 and self.ok:
            self.error = f'exit code: {p.exitcode!r}'
            self.ok = False
        
        return self.ok

