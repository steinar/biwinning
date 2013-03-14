#!/usr/bin/env python
import os
os.chdir(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))

import sys
from biwinning import app


if __name__ == '__main__':
    debug = 'debug' in sys.argv
    host = len(sys.argv) > 1 and sys.argv[1] or None
    app.run(debug=debug,host=host)
