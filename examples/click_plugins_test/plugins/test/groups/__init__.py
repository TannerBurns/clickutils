import click


@click.group(name='test_command1')
def test_command_group1():
    """Test command1 plugin"""
    pass


@test_command_group1.command()
def hey():
    print('hello world')


@click.command(name='test_command2')
def test_command_group2():
    """Test command2 plugin"""
    print('here')
    pass
