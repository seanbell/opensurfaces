#ifndef __TRIANGULATE_HPP
/**
 * Triangulate
 *
 * Takes a list of polylines and separates them into complex polygons such that
 * no two overlap.  This is equivalent to the 2D arrangement of the input line
 * segments.  Each complex polygon is represented as a list of triangles and a
 * list of poly-lines forming the boundary.  The input polygons can be
 * self-intersecting.
 *
 * The result is computed using the constrained Delaunay triangulation (CDT).
 * To reject the extra triangles created by the CDT, the arrangement of all the
 * input is computed.  Triangles not bounded by this arrangement are rejected.
 * To associate output polygons with input polylines, the arrangement of each
 * input polyline is computed.
 *
 * Input: Polylines as list of points, one polyline per line, separated by
 * whitespace, with an arbitrary ID as the first token, e.g.
 *     0 x1 y1 x2 y2 x3 y3
 *     1 x1 y1 x2 y2 x3 y3 x4 y4 x5 y5
 *     2 x1 y1 x2 y2 x3 y3 x4 y4
 * The id can be anything as long a it does not contain whitespace.  The input
 * may be terminated either with "END" on one line or by ending the file.  Any
 * text after "END" is ignored.
 *
 * Output: Flattened whitespace-separated list of vertices, triangles, and
 * lines separated by "|".  Each complex polygon is on its own line.  The first
 * group on each line is the IDs of the input polygons that contain it, or
 * nothing.
 * Triangles and lines are indices into the list of vertices e.g.
 *     0 | x0 y0 x1 y1 x2 y2 | v0 v1 v2 | v0 v1 v0 v2 v1 v2
 *     1 2 | x0 y0 x1 y1 x2 y2 x3 y3 | v0 v1 v2 v0 v2 v3 | v0 v1 v1 v2 v2 v3 v3 v0
 */

#include <stdexcept>
#include <iostream>
#include <fstream>
#include <boost/algorithm/string.hpp>

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>
#include <CGAL/Polygon_2.h>

#include <CGAL/Arr_segment_traits_2.h>
#include <CGAL/Arr_polyline_traits_2.h>
#include <CGAL/Arrangement_2.h>
#include <CGAL/Arr_naive_point_location.h>

#include <CGAL/Constrained_Delaunay_triangulation_2.h>
#include <CGAL/Constrained_triangulation_plus_2.h>

#include <CGAL/squared_distance_2.h>

using std::cout;
using std::cerr;
using std::cin;
using std::string;
using std::endl;
using std::vector;

// Kernel
typedef CGAL::Exact_predicates_exact_constructions_kernel K;
typedef CGAL::Polygon_2<K> Polygon_2;

// Arrangement
typedef CGAL::Arr_segment_traits_2<K>                      Segment_traits_2;
typedef CGAL::Arr_polyline_traits_2<Segment_traits_2>      Traits_2;
typedef Traits_2::Point_2                                  Point_2;
typedef Traits_2::Curve_2                                  Polyline_2;
typedef CGAL::Arrangement_2<Traits_2>                      Arrangement_2;
typedef CGAL::Arr_naive_point_location<Arrangement_2>      Point_location_2;
typedef Arrangement_2::Face_const_handle                   Arr_face_handle_2;

// Triangulations
typedef CGAL::Triangulation_vertex_base_2<K>                     Vb;
typedef CGAL::Constrained_triangulation_face_base_2<K>           Fb;
typedef CGAL::Triangulation_data_structure_2<Vb,Fb>              TDS;
typedef CGAL::Exact_intersections_tag                            Itag;
typedef CGAL::Constrained_Delaunay_triangulation_2<K, TDS, Itag> CDT_parent;
typedef CGAL::Constrained_triangulation_plus_2<CDT_parent>       CDT;


// Wrapper class to hold variables
class Triangulate {
	public:
		void load_polylines(std::istream &input);
		void build_triangulation();
		void build_out_triangle_components();
		void print_out_triangle_components();

	private:

		/// INPUT

		// storage for polygon points
		vector<vector<Point_2> > polyline_points;

		// poly-lines submitted by user
		vector<Polyline_2> polylines;

		// arrangement of each input polygon (to handle self-intersecting inputs)
		vector<std::pair<string, Arrangement_2> > poly_arr;

		// arrangement of all polylines
		Arrangement_2 arr;

		// constrained delaunay triangulation (CDT) of all input polyglines
		CDT cdt;

		// triangles in the CDT
		vector<CDT::Face_handle> tris;

		// map faces to their index in the list
		std::map<CDT::Face_handle, size_t> tri2index;

		// triangle midpoints
		vector<Point_2> tri_midpoints;

		// output polygons (connected component of triangles) as a list of
		// triangle indices
		vector<vector<size_t> > out_triangle_components;
};

inline bool
arrangement_contains(const Arrangement_2 &arr, const Point_2 &p) {
	Point_location_2 pl(arr);
	CGAL::Object obj = pl.locate(p);
	Arr_face_handle_2 f;
	return (CGAL::assign(f, obj) && !f->is_unbounded());
}

#define __TRIANGULATE_HPP
#endif /* __TRIANGULATE_HPP */
