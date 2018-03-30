#!/bin/bash
#
# Set up triangulate
#

# find the scripts directory (note the /..)
DIR="$( builtin cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
source $DIR/load_config.sh
cd "$REPO_DIR"

echo ""
echo "Installing cgal from source"
sudo apt-get install libboost1.48-dev libboost-thread1.48-dev libboost-system1.48-dev libgmp-dev libmpfr-dev
[[ -d opt/cgal ]] || git clone https://github.com/CGAL/cgal.git opt/cgal
cd opt/cgal
git checkout tags/releases/CGAL-4.6.3
cmake .
make
sudo make install
cd "$REPO_DIR"

echo ""
echo "Installing triangulate from source"
sudo apt-get install libboost-filesystem1.48-dev
cd triangulate
./build.sh
cd "$REPO_DIR"

echo "$0: done"
