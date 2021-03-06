# Copyright 2017 Carnegie Mellon University. See LICENSE.md file for terms.

# Ali Kidwai
# June 16, 2017
# Adapted from code written by Rotem Guttman and Joe Vessella
import random
import subprocess

import api
from tasks import task


class Shell(task.Task):
    """ Executes a random shell command from the configuration dictionary, or can execute all of them in sequence if the
    'script' parameter is set to true.
    """
    def __init__(self, config):
        """ Validates config and stores it as an attribute
        """
        self._config = config

    def __call__(self):
        """ Creates a Popen object from the subprocess module and sends a random command from config['commands'] to
        the commandline if script was False or unspecified, otherwise sends the commands in sequence.
        """
        if not self._config['script']:
            command = random.choice(self._config['commands'])
            self.run_command(command)
        else:
            for command in self._config['commands']:
                self.run_command(command)

    def cleanup(self):
        """ Doesn't need to do anything
        """
        pass

    def stop(self):
        """ This task should be stopped after running once

        Returns:
            True
        """
        return True

    def status(self):
        """ Called when status is polled for this task.

        Returns:
            str: An arbitrary string giving more detailed, task-specific status for the given task.
        """
        return ''

    @classmethod
    def parameters(cls):
        """ Returns a dictionary with the required and optional parameters of the class, with human-readable
        descriptions for each.

        Returns:
            dict of dicts: A dictionary whose keys are 'required' and 'optional', and whose values are dictionaries
                containing the required and optional parameters of the class as keys and human-readable (str)
                descriptions and requirements for each key as values.
        """
        params = {'required': {'commands': '[str]| A list of strings to send as commands, ex. ["ls -l", "cat README"]'},
                  'optional': {'script': 'bool| If True, execute the commands in order. Default is False.'}}
        return params

    @classmethod
    def validate(cls, config):
        """ Validates the given configuration dictionary. Makes sure that config['commands'] is a list of strings,
        but does not actually check if the commands are valid.

        Args:
            config (dict): The dictionary to validate. See parameters() for required format.

        Raises:
            KeyError: If a required configuration option is missing. The error message is the missing key.
            ValueError: If a configuration option's value is not valid. The error message is in the following format:
                key: value requirement

        Returns:
            dict: The dict given as the config argument
        """
        config = api.check_config(config, cls.parameters(), {'script': False})

        if not config['commands']:
            raise ValueError('commands: {} Cannot be empty'.format(str(config['commands'])))

        return config

    @staticmethod
    def run_command(command):
        # Check for the standard shell background job.
        background = command.strip()[-1] == '&'
        shell = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Should only wait for the process to terminate if it is not running in the background.
        if not background:
            shell.communicate()
