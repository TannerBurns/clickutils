import click
import json

class BaseClickViewCommand(click.Command):

    def __init__(self, *args, **kwargs):
        super(BaseClickViewCommand, self).__init__(*args, **kwargs)

    def invoke(self, ctx):
        ctx.params['self'] = self._cls
        return super(BaseClickViewCommand, self).invoke(ctx)

class clickviews(object):

    @staticmethod
    def command(name: str= None, **kwargs):
        return click.command(name, BaseClickViewCommand, **kwargs)


class BaseClickViewset(object):
    Name = 'BaseClickViewset'
    Version = None
    Viewset = None

    def __init__(self, name: str= '', **kwargs: dict):
        self.name = name or None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if isinstance(self.Viewset, dict):
            for key, value in self.Viewset.items():
                setattr(self, key, value)

    def __call__(self, *args: list, **kwargs: dict):
        group = click.Group(name=self.name, **kwargs)
        for method in [m for m in dir(self) if not m.startswith('__') and not m.endswith('__')]:
            attr = getattr(self, method)
            if type(attr) == BaseClickViewCommand:
                attr._cls = self
                group.add_command(attr)
        return group

    def echoattr(self, attribute: str):
        if hasattr(self, attribute):
            value = getattr(self, attribute)
            if isinstance(value, dict):
                print(json.dumps(value, indent=2))
            elif isinstance(value, list):
                print('\n'.join(value))
            else:
                print(value)
        else:
            print(f'Error: Unable to find attribute with name {attribute!r}')


class AbstractClickViewset(BaseClickViewset):
    Name = 'AbstractClickViewset'

    @clickviews.command(name='echo')
    @click.option('--attribute', '-a', type=str, help='echo attribute if exists')
    def echo(self, attribute: str):
        """Attempt to read and print attributes by name

        Args:
            attribute {str} -- attribute name to attempt and read
        """
        self.echoattr(attribute)

    @clickviews.command(name='group_version')
    def version(self):
        """Print version string of group"""
        self.echoattr('Version')








