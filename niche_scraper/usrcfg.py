# I love the user-config package, and it is VERY close to exactly what I need.
# but there are some critical changes, and forking the project is more than
# I want to take on at this time. I will contribute back these changes, but
# not for this simple of a tool. This this one file is under the GPLv3 license 
# in compliance with the original maintainers wishes.

# Origional Source: https://github.com/nihlaeth/user_config/
# GPLv3 Project license: https://github.com/nihlaeth/user_config/blob/master/LICENSE
# Code Changes:
#  * copied and then monkey patched the ConfigElement.construct_parser method to
#      allow for setting the default argparser value and if the option is required 
#      when using the cli.
#  * copied and modified the constructor of the Config class, overriding it,
#      to display the current default values, (could be from read in existing config file,)
#      and remove hte printing option.
#  * copied and modified the user_config/ini.py ini writer code to write to file.

import os, sys, os.path
from user_config import *
from six import string_types
import argparse

# I am not proud of this.
def _construct_parser(self, parser):
    """
    """
    name = []
    if self._short_name is not None:
        name.append(self._short_name)
    if self._long_name is not None:
        name.append(self._long_name)
    else:
        name.append("--{}".format(self.element_name))
    type_ = self.type_ if self.action == 'store' else self.subtype
    # argparse attempts to convert, which does not end well with
    # python2 basestr
    if issubclass(type_, string_types):
        type_ = str

    parser.add_argument(
        *name,
        action=self.action,
        #nargs=1,
        default=self._value,
        type=type_,
        choices=None,
        required=False if self._value is not None else self.required,
        help=self.doc)

ConfigElement.construct_parser = _construct_parser


def _print_item(fileobj, key, item, value):
    """Print single key value pair."""
    # print docstring
    if item.doc is not None:
        doc_string = item.doc.split('\n')
        for line in doc_string:
            print("## {}".format(line), file=fileobj)

    # TODO: display data type
    # print default
    if item.has_default():
        # handle multiline strings
        if item.type_ == list:
            lines = ['- {}'.format(thing) for thing in item.get_default()]
        else:
            lines = str(item.get_default()).split('\n')
        print("# {} = {}".format(key, lines[0]), file=fileobj)
        if len(lines) > 1:
            for line in lines[1:]:
                print("#     {}".format(line), file=fileobj)
    else:
        if item.required:
            print("## REQUIRED", file=fileobj)
        print("# {} = ".format(key), file=fileobj)

    # print current value
    if value is None and item.required:
        print("{} = ".format(key), file=fileobj)
    elif value is not None and value != item.get_default():
        # handle multiline strings
        if item.type_ == list:
            lines = ['- {}'.format(thing) for thing in value]
        else:
            lines = str(value).split('\n')
        print("{} = {}".format(key, lines[0]), file=fileobj)
        if len(lines) > 1:
            for line in lines[1:]:
                print("    {}".format(line), file=fileobj)
    print("", file=fileobj)

def ini_write(fileobj, elements, doc):
    """
    """
    # print config class docstring
    if doc is not None:
        doc_string = doc.split('\n')
        for line in doc_string:
            print("## {}".format(line), file=fileobj)
        print("", file=fileobj)

    for section in elements:
        print("[{}]".format(section), file=fileobj)
        # print docstring and optional status
        if elements[section].doc is not None:
            doc_string = elements[section].doc.split('\n')
            for line in doc_string:
                print("## {}".format(line), file=fileobj)
        if not elements[section].required:
            print("## OPTIONAL_SECTION", file=fileobj)
        if elements[section].doc is not None or not elements[section].required:
            print("", file=fileobj)

        keys = elements[section].get_elements()
        for key in keys:
            _print_item(fileobj, key, keys[key], keys[key].get_value())
        print("", file=fileobj)

class UserConfig(Config):
    def __init__(
        self,
        file_name="config",
        global_path=None,
        user_path=None,
        cli=False):
        if self.application is None:
            raise AttributeError(
                'application not set, please provide an application name')
        if self.author is None:
            raise AttributeError(
                'author not set, please provide an application author')
        # validate _elements
        self._validate(self._elements)
        # read global config
        if global_path is None or user_path is None:
            paths = AppDirs(self.application, self.author, self.version)
        if global_path is None:
            global_path = Path(paths.site_config_dir)
        global_path = global_path.joinpath(
            "{}.{}".format(file_name, self._extension))
        if global_path.is_file():
            self._read(global_path, self._elements)
        # read user config
        self.user_cache_dir = Path(paths.user_config_dir).joinpath('cache')
        if user_path is None:
            user_path = Path(paths.user_config_dir)
        user_path = user_path.joinpath(
            "{}.{}".format(file_name, self._extension))
        if user_path.is_file():
            self._read(user_path, self._elements)
        do_save = False

        # construct a commandline parser
        # always construct it so we can do gooey stuff
        self.parser = argparse.ArgumentParser(
            prog=self.application,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="{}\n\n{}\n{}\n{}".format(
                self.__doc__,
                "Command line arguments overwrite configuration found in:",
                user_path,
                global_path))
        self.parser.add_argument(
            '--save',
            action='store_const',
            const=True,
            default=False,
            required=False,
            dest='__save__',
            help="Save the configuration options to {}".format(user_path),)
        for element in self._elements:
            self._elements[element].construct_parser(self.parser)
        
        if cli:
            command_line_arguments = vars(self.parser.parse_args())
            do_save = command_line_arguments['__save__']

            # fetch command line argument data
            for element in self._elements:
                self._elements[element].extract_data_from_parser(
                    command_line_arguments)

        # validate _data
        for element in self._elements:
            self._elements[element].validate_data()

        # save out the new config
        if do_save:
            os.makedirs(os.path.dirname(user_path), exist_ok=True)
            with open(user_path, "w") as f:
                ini_write(f, self._elements, self.__doc__)
        elif cli:
            self.parser.print_help()

