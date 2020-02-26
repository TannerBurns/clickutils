import os
import click

from clickutils import click_loader

@click.group()
def cli():
    '''click_plugins'''

@click_loader.group(os.path.dirname(os.path.abspath(__file__)), name='plugins', debug=False)
def plugins_group():
    '''click_plugins test plugins'''
    pass


cli.add_command(plugins_group)

if __name__ == '__main__':
    cli()