import os
import click

from typing import Callable

from clickutils import load_commands_from_path, load_commands_from_directory

class load_groups_and_commands(object):

    def __init__(self, filepath: str, verbose: bool= False):
        self.verbose = verbose
        if os.path.exists(filepath):
            self.filepath = filepath
        else:
            raise TypeError(f'Argument must be a valid filepath. Given path: {filepath!r} was not valid')

    
    def __call__(self, fn: Callable):
        if type(fn) == click.core.Group and self.filepath:
            if os.path.isfile(self.filepath):
                load_commands_from_path(fn, self.filepath, verbose=self.verbose)
            if os.path.isdir(self.filepath):
                load_commands_from_directory(fn, self.filepath, verbose=self.verbose)
        else:
            msg = f'Self is of type: {type(self).__name__!r} and not {f"click.Group"!r}.'
            msg += f'Please make sure decorator is above click decorators.'
            raise TypeError(msg)
        
        return fn    

    