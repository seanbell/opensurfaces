#!/bin/bash
if [ ! -d ~/mitsuba ]; then
	echo "Mitsuba is not installed!"
	exit 1
fi

ln -s -f $(pwd) ~/mitsuba/src/utils/prefilter

echo "Sorry, this isn't fully automated..."
echo "Add these lines:"
echo "    plugins += env.SharedLibrary('prefilter', ['prefilter/prefilter.cpp'])"
echo "    plugins += env.SharedLibrary('encodehdr', ['prefilter/encodehdr.cpp'])"
echo "to the middle of this file:"
echo "    ~/mitsuba/src/utils/SConscript"
echo "Then rebuild mitsuba."
