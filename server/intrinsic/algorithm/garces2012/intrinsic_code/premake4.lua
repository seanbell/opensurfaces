-- A solution contains projects, and defines the available configurations
--
solution "garces2012"

	-- global config
	language "C++"
	configurations { "release" }
	location "build"
	includedirs { "include", "/usr/local/include", "/usr/include", "lib/IML++", "lib/kmlocal/src" }
	libdirs { "/usr/lib", "/usr/local/lib", "lib/kmlocal/build" }
	flags { "Symbols" }

	-- Boost
	links { "boost_system", "boost_filesystem", "boost_date_time", "boost_thread" }

	-- release
	configuration { "release" }
		kind "ConsoleApp"
		flags { "OptimizeSpeed" }
		buildoptions { "-march=native", "-mtune=native", "-mfpmath=sse",
					   "-mmmx", "-msse", "-msse2", "-msse3", "-mssse3", "-msse4" }
	    targetdir "build/release"

	project "garces2012"
		files { "include/**.h", "src/**.cpp",
				"lib/kmlocal/src/KM_ANN.cpp",
				"lib/kmlocal/src/KMeans.cpp",
				"lib/kmlocal/src/KMterm.cpp",
				"lib/kmlocal/src/KMrand.cpp",
				"lib/kmlocal/src/KCutil.cpp",
				"lib/kmlocal/src/KCtree.cpp",
				"lib/kmlocal/src/KMdata.cpp",
				"lib/kmlocal/src/KMcenters.cpp",
				"lib/kmlocal/src/KMfilterCenters.cpp",
				"lib/kmlocal/src/KMlocal.cpp"
			}

	--project "oh2001"
		--files { "include/**.h", "src/**.cpp" }
		--files { "main-src/oh2001.cpp" }

	--project "delong2012-crf"
		--files { "include/**.h", "src/**.cpp" }
		--files { "main-src/delong2012-crf.cpp" }
		--links { "cnpy" }

	--project "krahenbuhl2013-crf"
		--files { "include/**.h", "src/**.cpp" }
		--files { "main-src/krahenbuhl2013-crf.cpp" }
		--links { "cnpy" }

	--project "floodfill"
		--files { "include/**.h", "src/**.cpp" }
		--files { "main-src/floodfill.cpp" }
		--links { "cnpy" }

	--project "model-v2_2"
		--files { "include/**.h", "src/**.cpp" }
		--files { "main-src/model-v2_2.cpp" }
		--links { "cnpy" }
