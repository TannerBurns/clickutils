import click

from clickutils.views import AbstractClickViewset, clickviews

@click.group(name='test_command1')
def test_command_group1():
    '''Test command1 plugin'''
    pass


@click.command()
def hey():
    print('hello world')


class UserDefinedViewset(AbstractClickViewset):
    Name = 'NewClickViewset'
    Version = '1.0.0'
    Viewset = {'users': ['user1', 'user2', 'user3']}

    @clickviews.command(name='another_command')
    def another_command(self):
        print('defined another user command that can interact with Viewset')

@UserDefinedViewset(name='test_command2')
def test_command_group2():
    '''Test command2 plugin'''
    pass
