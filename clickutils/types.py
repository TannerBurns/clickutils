import click
import re
import os

from typing import Union, List


SHA256_PATTERN = re.compile('[A-Fa-f0-9]{64}')


class Sha256ParamType(click.ParamType):
    name = 'sha256'

    def convert(self, value, param, ctx) -> Union[str, List[str]]:
        # check if value is a string
        if isinstance(value, str):
            # check if value exists on system
            if os.path.exists(value):
                # confirm value is a file
                if os.path.isfile(value):
                    # return all found sha256
                    with open(value, 'r') as fin:
                        return SHA256_PATTERN.findall(fin.read())
                else:
                    # report value is not a value file
                    self.fail(f'expected path to be a file, got {value!r}', param, ctx)
            else:
                # value is not of type file, treat as valid string and check if sha256
                if SHA256_PATTERN.match(value):
                    return value
                # report value is not a valid sha256
                else:
                    self.fail(f'{value!r} is not a value sha256', param, ctx)
        # report that types of non string cannot be converted to sha256
        else:
            self.fail(f'expected string for sha256 type conversion, got {value!r} of type {type(value).__name__}')

SHA256_TYPE = Sha256ParamType()