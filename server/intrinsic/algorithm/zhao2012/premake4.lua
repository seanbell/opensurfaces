-- A solution contains projects, and defines the available configurations
--
solution "triangulate"

	-- global config
	configurations { "release", "debug" }
	location "build"
	includedirs {
		"/usr/local/MATLAB/R2011b/extern/include",
		"/home/sbell/opt/OpenCV-2.1.0/include",
	    "/usr/include",
	}
	libdirs {
		"/usr/local/MATLAB/R2011b/bin/glnxa64",
		"/usr/local/MATLAB/R2011b/sys/os/glnxa64",
		"/home/sbell/opt/OpenCV-2.1.0/build/lib",
		"/usr/lib"
	}
	flags { "Symbols" }

	links { "boost_filesystem", "boost_system" }
	links { "eng", "mx" }

	links { "blas" }
	links { "ann" }

	-- OpenCV
	--links { "opencv_core", "opencv_imgproc", "opencv_highgui", "opencv_ml", "opencv_video",
			--"opencv_features2d", "opencv_calib3d", "opencv_objdetect", "opencv_contrib",
			--"opencv_legacy", "opencv_flann" }
	links { "cxcore", "cv", "highgui" }

	-- release: make config=debug
	configuration { "release" }
		flags { "OptimizeSpeed" }
		--buildoptions { "-march=native", "-mtune=native", "-mfpmath=sse",
					   --"-mmmx", "-msse", "-msse2", "-msse3", "-mssse3", "-msse4" }

	-- debug: make config=debug
	configuration { "debug" }
	   defines { "DEBUG" }
	   buildoptions { "-g3", "-O0" }

   -- build locally
   project "intrinsic_soe"
      kind "ConsoleApp"
      language "C++"
      files { "intrinsic_soe_src/**.h", "intrinsic_soe_src/**.cpp" }
      links { }

      configuration { "release" }
		   targetdir "build/release"

      configuration { "debug" }
          targetdir "build/debug"
