# ************************************************************************************* #
#
# This file starts the app DashVolcano.
# Type the command: python run.py
#
# Author: F. Oggier
# Last update: 23 Sep 2023
# ************************************************************************************* #

import index

if __name__ == '__main__':
    index.app.run_server(debug=True, host='127.0.0.1')
