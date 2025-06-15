'''Provides import context for the target module.'''
import os
import sys
_PROJECT_DIR = os.path.join(os.path.dirname(__file__), os.path.pardir)
sys.path.insert(0, os.path.abspath(_PROJECT_DIR))

import src