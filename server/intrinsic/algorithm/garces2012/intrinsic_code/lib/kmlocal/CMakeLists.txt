set(srcs_kmlocal
	src/KM_ANN.cpp
	src/KMeans.cpp
	src/KMterm.cpp
	src/KMrand.cpp
	src/KCutil.cpp
	src/KCtree.cpp
	src/KMdata.cpp
	src/KMcenters.cpp
	src/KMfilterCenters.cpp
	src/KMlocal.cpp
)

include_directories(src)


add_executable(kmltest ${srcs_kmlocal} src/kmltest.cpp)
	
add_executable(kmlsample ${srcs_kmlocal} src/kmlsample.cpp)
	
add_executable(kmlminimal ${srcs_kmlocal} src/kmlminimal.cpp)
	
