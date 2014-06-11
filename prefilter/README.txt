This directory contains the code to prefilter an environment map
for rendering in the browser.  It uses Mitsuba (www.mitsuba-renderer.org);
the scripts currently assume you are using Linux.

You will need to download ennis.exr from the "High-Resolution Light Probe Image Gallery",
as it is  used for the environment maps: http://gl.ict.usc.edu/Data/HighResProbes/

THIS IS A MITSUBA PLUGIN -- TO SET UP, SYMLINK INTO MITSUBA:
	cd <mitsuba>/src/utils # mitsuba directory
	ln -s <...>/prefilter  # this directory

ADD THIS TO <mitsuba>/src/utils/SConscript:
	plugins += env.SharedLibrary('prefilter', ['prefilter/prefilter.cpp'])

ADD THIS TO <mitsuba>/src/utils/CMakeLists.txt:
	add_utility(prefilter      prefilter/prefilter.cpp)

RUN:
	python generate-materials-vwd.py
