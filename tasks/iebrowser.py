# Copyright 2017 Carnegie Mellon University. See LICENSE.md file for terms.

# Ali Kidwai
# July 26, 2017
# Adapted from code written by Rotem Guttman and Joe Vessella

import functools
import platform
import queue
import random
import threading
import time
import traceback

import psutil
try:
    import pythoncom
    import win32api
    import win32com.client
    import win32con
    import win32process
except ImportError:
    # Tasks must be importable on any platform.
    pass

import api
from tasks import browser


class IEManager(object):
    """ Allows different InternetExplorer tasks to share one instance of Internet Explorer. Spawns a new consumer thread
    to visit sites so that UserSim doesn't block while waiting for sites to load.
    """
    _action_queue = None
    _ie = None
    _persist = True

    def __new__(cls):
        """ Initialize the action queue and spawn a consumer thread if the IEManager hasn't already been created.
        """
        if cls._action_queue is None:
            cls._action_queue = queue.Queue()

            t = threading.Thread(target=cls._action_executor)
            t.daemon = True
            t.start()

            cls._action_queue.put((cls._start_ie, 0, 10))
        return cls

    @classmethod
    def _action_executor(cls):
        """ Target function for the consumer thread. Executes actions from the action queue. If the main User Sim thread
        calls IEManager.close_browser(), then the consumer thread will finish any actions remaining on the queue, close
        the browser window, and reset the class variables.
        """
        while cls._persist or not cls._action_queue.empty():
            try:
                # Without the timeout, this would block forever if cls._persist is set to False after the get call
                # already started.
                action, task_id, delay = cls._action_queue.get(timeout=1)
            except queue.Empty:
                continue
            else:
                try:
                    action()
                except Exception:
                    api.add_feedback(task_id, traceback.format_exc())
                time.sleep(delay)

        cls._action_queue = None
        cls._persist = True

        try:
            cls._ie.Quit()
        except Exception:
            # Try to kill it. If not, oh well.
            try:
                for process in psutil.process_iter():
                    if 'iexplore' in process.name():
                        process.kill()
            except Exception:
                pass
        finally:
            cls._ie = None

    @classmethod
    def get(cls, site, task_id, delay=0):
        """ Add a _visit_site action to the action queue.
        """
        # Use functools.partial so that the action doesn't need any arguments
        cls._action_queue.put((functools.partial(cls._visit_site, site), task_id, delay))

    @classmethod
    def status(cls):
        if not cls._ie:
            return 'IE has not yet been fully started.'
        if cls._ie.Busy:
            return 'IE reports that it is loading a web page.'
        else:
            return 'IE is idle.'

    @classmethod
    def close_browser(cls):
        """ Sets _persist to False so that the consumer thread breaks out of its loop.
        """
        cls._persist = False

    @classmethod
    def _start_ie(cls):
        """ Create an instance of Internet Explorer.
        """
        pythoncom.CoInitialize()
        cls._ie = win32com.client.gencache.EnsureDispatch('InternetExplorer.Application')
        cls._ie.Visible = True

    @classmethod
    def _visit_site(cls, site):
        """ Navigate to site and wait for Internet Explorer to either time out or finish loading.
        """
        cls._ie.Navigate(site)
        cls._wait_for_ie()

    @classmethod
    def _wait_for_ie(cls):
        """ Wait for Internet Explorer to either time out or finish loading. If it times out, try to terminate it.
        """
        start = time.time()
        while cls._ie.Busy or cls._ie.Document.readyState != 'complete':
            if time.time() - start >= 200: # IE timed out; terminate it.
                _, pid = win32process.GetWindowThreadProcessId(cls._ie.HWND)
                handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
                if handle:
                    win32api.TerminateProcess(handle, 0)
                    win32api.CloseHandle(handle)


class IEBrowser(browser.Browser):
    """ Opens an instance of Internet Explorer and visits a website at random from the configuration. Windows-only.
    """
    def __init__(self, config):
        if not platform.system() == 'Windows':
            raise OSError('This task is only compatible with Windows.')
        super().__init__(config)
        self._close = config['close_browser']
        self._driver = IEManager()

    def __call__(self):
        super().__call__()
        if self._close:
            self._driver.close_browser()

    @classmethod
    def parameters(cls):
        """ Returns a dictionary with the required and optional parameters of the class, with human-readable
        descriptions for each.

        Returns:
            dict of dicts: A dictionary whose keys are 'required' and 'optional', and whose values are dictionaries
                containing the required and optional parameters of the class as keys and human-readable (str)
                descriptions and requirements for each key as values.
        """
        params = super().parameters()
        params['optional']['close_browser'] = 'bool| If True, the browser window will close after visiting a website. '\
                                              'Defaults to False.'
        return params

    @classmethod
    def validate(cls, config):
        """ Validates the given configuration dictionary. Makes sure that each site in config['sites'] is a string, but
        doesn't actually check to see if they are valid web addresses.

        Args:
            config (dict): The dictionary to validate. Its keys and values are subclass-specific.

        Raises:
            KeyError: If a required configuration option is missing. The error message is the missing key.
            ValueError: If a configuration option's value is not valid. The error message is in the following format:
                key: value requirement

        Returns:
            dict: The dict given as the config argument with missing optional parameters added with default values.
        """
        extra_defaults = {'close_browser': False}
        return super().validate(config, extra_defaults=extra_defaults)
