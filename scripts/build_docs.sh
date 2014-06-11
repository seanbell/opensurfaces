#!/bin/bash
#
# Build the docs (vieable publicly at http://SERVER_NAME/docs).
#
# You can view them in docs/_build/html/
#

DIR="$( builtin cd "$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )" && pwd )"
source "$DIR/load_config.sh"

if [[ ! -d $VENV_DIR ]]; then
	echo "Error: virtualenv not yet set up.  Please run the installer."
	exit 1
fi

builtin cd "$REPO_DIR/docs"
make html
