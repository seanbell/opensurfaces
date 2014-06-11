#!/bin/bash
#
# Builds the triangulate program
#

VERSION_H=/usr/local/include/CGAL/version.h
if [[ -f $VERSION_H ]]; then
	version=$(grep '^#define CGAL_VERSION ' $VERSION_H | awk '{print $3}')
	if [[ -z "$version" ]]; then
		echo "Could not find CGAL_VERSION in header $VERSION_H"
	elif (( $(echo "$version < 4.1" | bc -l) )); then
		echo "CGAL version too old: $version"
	else
		set -e
		./premake4 gmake
		cd build
		make
		cd -
		ln -sf build/release/triangulate
		chmod 777 triangulate build/release/triangulate
		exit 0
	fi
else
	echo "CGAL not found in /usr/local"
fi

echo "Please install CGAL (version >= 4.1, < 5) to the default directory (prefix /usr/local)"
echo ""
echo "Visit: https://www.cgal.org/download.html"
echo ""
exit 1
