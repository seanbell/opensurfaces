-- A solution contains projects, and defines the available configurations
--
solution "triangulate"

	-- global config
	configurations { "release", "debug" }
	location "build"
	includedirs { "include", "/usr/local/include", "/usr/include" }
	libdirs { "/usr/lib", "/usr/local/lib" }
	flags { "Symbols", "FatalWarnings", "ExtraWarnings" }

	-- Stack traces
	linkoptions { "-rdynamic" }

	-- Eigen
	includedirs { "/usr/include/eigen" }

	-- OpenMP
	links { "gomp" }
	buildoptions { "-fopenmp" }

	-- Boost
	links { "boost_system", "boost_filesystem", "boost_date_time", "boost_thread" }

	-- CGAL
	buildoptions { "-frounding-math" }
	defines { "CGAL_HAS_THREADS" }
	links { "gmp", "CGAL", "CGAL_Core", "mpfr" }

	-- release: make config=debug
	configuration { "release" }
		flags { "OptimizeSpeed" }
		buildoptions { "-march=native", "-mtune=native", "-mfpmath=sse",
					   "-mmmx", "-msse", "-msse2", "-msse3", "-mssse3", "-msse4" }

	-- debug: make config=debug
	configuration { "debug" }
	   defines { "DEBUG" }
	   buildoptions { "-g3", "-O0" }


   -- build locally
   project "triangulate"
      kind "ConsoleApp"
      language "C++"
      files { "include/**.h", "src/**.cpp" }
      links { }

      configuration { "release" }
		   targetdir "build/release"

      configuration { "debug" }
          targetdir "build/debug"
