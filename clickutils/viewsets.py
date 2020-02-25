import click
import json

from typing import Union, Any

class ClickViewCommand(click.Command):
    """Overloaded click.Command to set ctx.params['self'] as the object, this will be set during a proper call to Viewset

    Args:
        *args {list} -- list of arguments for class
        **kwargs {dict} -- dictionary of named arguments
    """

    def __init__(self, *args: list, **kwargs: dict):
        super(ClickViewCommand, self).__init__(*args, **kwargs)
        self._cls = None

    def invoke(self, ctx: click.Context):
        """Overloaded invoke, sets the ctx.params['self'] value

        Args:
            ctx: {click.Context} -- current click.Context

        Returns:
            super(.*).invoke(ctx) -- value from invoke call
        """
        ctx.params['self'] = self._cls
        return super(ClickViewCommand, self).invoke(ctx)

class clickmixins(object):

    @staticmethod
    def command(name: str= None, **kwargs: dict):
        """decorator for creating a click command tied to a viewset - ClickViewCommand, click.command

        Args:
            name {str} -- name to give command
            **kwargs {dict} -- optional arguments passed to click.command

        Returns:
            click.Command -- new click.Command with cls=ClickViewCommand
        """
        return click.command(name, ClickViewCommand, **kwargs)


class BaseClickViewset(object):
    """BaseClickViewset - ClickViewCommands added to a viewset will be able to tie groups with objects than can be
        overloaded by users to be able to query different content

    Args:
        *args {list} -- list of positional arguments
        **kwargs {dict} optional arguments, if name is given it will be used as  the group name
    """
    Name: str
    Version: Union[str, int, float]
    Viewset: Any
    commands: tuple
    hidden_commands: tuple

    def __init__(self, *args, **kwargs: dict):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __call__(self, *args: list, **kwargs: dict):
        """invoked on command call

        Args:
            *args {list} -- list of arguments
            **kwargs {dict} -- dictionary of named arguments

        Returns:
            group {click.Group} -- new group with any attribute commands added
        """
        group = click.Group(name=self.name, **kwargs)
        for method in [m for m in dir(self) if not m.startswith('__') and not m.endswith('__')]:
            attr = getattr(self, method)
            if type(attr) == ClickViewCommand and (hasattr(self, 'commands') and any(c in method for c in self.commands)):
                if hasattr(self, 'hidden_commands') and any(hc in method for hc in self.hidden_commands):
                    attr.hidden=True
                attr._cls = self
                group.add_command(attr)
        self.convert()
        return group


    def convert(self):
        """convert Viewset into object attributes; defined by user
        """


    def echoattr(self, attribute: str, list_delimiter:str='\n', name_only:bool=False, show_type:bool=False):
        """print an attribute to stdout

        Args:
            attribute {str} -- attribute name
            list_delimiter {str} -- delimiter to join list with [default: '\n']
            show_name {bool} -- option to show attribute name on print
            show_type {bool} -- option to show type of attribute on print

        """
        if hasattr(self, attribute):
            value = getattr(self, attribute)

            msg = f'{attribute!r} '

            if not name_only:
                if show_type:
                    msg += f'{type(value).__name__!r} '

                if isinstance(value, dict):
                    msg += json.dumps(value, indent=2)
                elif isinstance(value, (tuple, list)):
                    msg += list_delimiter.join((str(v) for v in value))
                else:
                    msg += value if value else ''

            print(msg)
        else:
            print(f'Error: Unable to find attribute with name {attribute!r}')


class AbstractClickViewset(BaseClickViewset):
    """AbstractClickViewset
        AbstractViewset for a command line interface - inherit class to reuse commands
            echo - print specified attributes known to invoked class command
            list - list all attributes known to invoked class command
            version (command_version) - print version of command (if set) for invoked class command
    """
    Name = 'AbstractClickViewset'
    commands = ('echo', 'list', 'version')

    @clickmixins.command(name='echo')
    @click.option('--attribute', '-a', type=str,
        help='echo attribute if exists')
    @click.option('--list_delimiter', '-ld', type=str, default='\n', show_default=True,
        help='Delimiter to use for list join')
    def echo(self, attribute: str, list_delimiter: str):
        """Attempt to read and print attributes by name

        Args:
            attribute {str} -- attribute name to attempt and read
        """
        self.echoattr(attribute, list_delimiter=list_delimiter)

    @clickmixins.command(name='list')
    @click.option('--values', '-v', is_flag=True, type=bool, default=False, show_default=True,
        help='Show values for the attribute during output')
    @click.option('--types', '-t', is_flag=True, type=bool, default=False, show_default=True,
        help='Show attribute types in print out')
    @click.option('--named', '-n', is_flag=True, type=bool, default=False, show_default=True,
        help='Print Python named attributes: ex: __doc__')
    def list(self, values:bool, types:bool, named: bool):
        """Print the list of non callable attributes for the invoked command

        Args:
            values {bool} -- flag for show value of attribute being printed [default:False]
            types {bool} -- flag for show the type of attribute being printed [default:False]
            named {bool} -- flag to show Python named functions ex: __doc__ [default:False]

        """
        for attr in dir(self):
            if callable(getattr(self, attr)) or (attr.startswith('__') and attr.endswith('__') and not named):
                continue
            self.echoattr(attr, list_delimiter=', ', name_only=not values, show_type=types)


    @clickmixins.command(name='command_version')
    def version(self):
        """Print version string of group"""
        self.echoattr('Version')







