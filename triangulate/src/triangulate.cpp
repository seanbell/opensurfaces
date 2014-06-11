#include <triangulate.hpp>
#include <union_find.hpp>

/**
 * See include/triangulate.hpp for documentation
 */

int main(int argc, char **argv) {
	cout.precision(16);

	Triangulate t;
	if (argc == 2) {
		std::ifstream ifs(argv[1]);
		t.load_polylines(ifs);
	} else {
		t.load_polylines(cin);
	}
	t.build_triangulation();
	t.build_out_triangle_components();
	t.print_out_triangle_components();
}

void Triangulate::load_polylines(std::istream &input) {
	string line;
	while (std::getline(input, line)) {
		boost::trim(line);
		if (line == "END") break;
		std::stringstream ss(line);

		polyline_points.push_back(vector<Point_2>());
		vector<Point_2> &points = polyline_points.back();

		// id first
		string id;
		if (!(ss >> id)) break;

		// read points
		while (true) {
			double x, y;
			if (!(ss >> x)) break;
			if (!(ss >> y)) {
				cerr << "Note: extra number ignored (id: " << id << ")" << endl;
				break;
			}
			Point_2 p(x, y);
			if (points.empty() || squared_distance(p, points.back()) > 0) {
				points.push_back(p);
			} else {
				cerr << "Note: degenerate segment rejected (id: " << id << ")" << endl;
			}
		}

		if (points.size() >= 3) {
			// for the polyline, close the polygon if not already closed
			if (squared_distance(points[0], points.back()) > 0) {
				points.push_back(points[0]);
			} else {
				cerr << "Note: degenerate end segment rejected (id: " << id << ")" << endl;
			}

			polylines.push_back(Polyline_2(points.begin(), points.end()));

			// construct an arrangement for each polygon
			poly_arr.push_back(std::make_pair(id, Arrangement_2()));
			CGAL::insert(poly_arr.back().second, polylines.back());
			if (!poly_arr.back().second.is_valid()) {
				cerr << "Note: rejected invalid polyline arrangement (id: " << id << ")" << endl;
				poly_arr.pop_back();
			}
		} else {
			cerr << "Note: single-point poly-line rejected (id: " << id << ")" << endl;
			continue;
		}
	}
}

void Triangulate::build_triangulation() {

	// build cdt
	for (size_t i = 0; i < polylines.size(); ++i) {
		vector<Point_2> &points = polyline_points[i];
		const size_t npoints = points.size();
		for (size_t j = 0; j < npoints; ++j) {
			cdt.insert_constraint(points[j], points[(j+1) % npoints]);
		}
	}
	if (!cdt.is_valid()) {
		throw new std::runtime_error("Invalid triangulation");
	}

	// build arrangement
	CGAL::insert(arr, polylines.begin(), polylines.end());
	if (!arr.is_valid()) {
		throw new std::runtime_error("Invalid arrangement");
	}

	// extract triangles inside the arrangement
	for (CDT::Finite_faces_iterator fit = cdt.finite_faces_begin();
	        fit != cdt.finite_faces_end(); ++fit) {

		// find triangle midpoint
		Point_2 midpoint(
			(fit->vertex(0)->point().x() + fit->vertex(1)->point().x() + fit->vertex(2)->point().x()) / 3,
			(fit->vertex(0)->point().y() + fit->vertex(1)->point().y() + fit->vertex(2)->point().y()) / 3
		);

		// keep triangle only if its midpoint is bounded inside the arrangement
		if (arrangement_contains(arr, midpoint)) {
			size_t tri_idx = tris.size();
			tris.push_back(fit);
			tri2index[fit] = tri_idx;
			tri_midpoints.push_back(midpoint);
		}
	}
}

void Triangulate::build_out_triangle_components() {
	// merge neighboring triangles from the same component
	UnionFind uf_tris(tris.size());
	for (size_t i = 0; i < tris.size(); ++i) {
		CDT::Face_handle &tri = tris[i];
		for (size_t j = 0; j < 3; ++j) {
			const CDT::Face_handle &neighbor = tri->neighbor(j);
			if (!cdt.is_infinite(neighbor) && !tri->is_constrained(j)) {
				const size_t neighbor_idx = tri2index[neighbor];
				uf_tris.unionSets(i, neighbor_idx);
			}
		}
	}

	// find connected components
	uf_tris.findSets(out_triangle_components, 1);
}

void Triangulate::print_out_triangle_components() {

	// output polygons
	for (size_t op_idx = 0; op_idx < out_triangle_components.size(); ++op_idx) {
		vector<size_t> &out_triangles = out_triangle_components[op_idx];
		if (out_triangles.empty()) {
			continue;
		}

		vector<CDT::Vertex_handle> verts;
		std::map<CDT::Vertex_handle, size_t> vert2index;

		// print polygon IDs
		for (size_t i = 0; i < poly_arr.size(); ++i) {
			bool contains_all = true;
			for (size_t j = 0; j < out_triangles.size(); ++j) {
				const Point_2 &p = tri_midpoints[out_triangles[j]];

				if (!arrangement_contains(poly_arr[i].second, p)) {
					contains_all = false;
					break;
				}
			}

			if (contains_all) {
				cout << " " << poly_arr[i].first;
			}
		}
		cout << " |";

		// print vertices
		for (size_t i = 0; i < out_triangles.size(); ++i) {
			CDT::Face_handle &tri = tris[out_triangles[i]];

			for (size_t j = 0; j < 3; ++j) {
				const CDT::Vertex_handle &v = tri->vertex(j);

				if (vert2index.find(v) == vert2index.end()) {
					size_t idx = verts.size();
					verts.push_back(v);
					vert2index[v] = idx;
					cout << " " << CGAL::to_double(v->point().x())
						 << " " << CGAL::to_double(v->point().y());
				}
			}
		}
		cout << " |";

		// print bag of triangles
		for (size_t i = 0; i < out_triangles.size(); ++i) {
			CDT::Face_handle &tri = tris[out_triangles[i]];
			for (size_t j = 0; j < 3; ++j)
				cout << " " << vert2index.at(tri->vertex(j));
		}
		cout << " |";

		// print bag of edges along border
		for (size_t i = 0; i < out_triangles.size(); ++i) {
			CDT::Face_handle &tri = tris[out_triangles[i]];

			// check triangle neighbors
			for (size_t j = 0; j < 3; ++j) {
				const CDT::Face_handle &neighbor = tri->neighbor(j);

				if (cdt.is_infinite(neighbor) || tri->is_constrained(j)) {

					// found an edge
					const size_t v0 = vert2index[tri->vertex(CDT::ccw(j))];
					const size_t v1 = vert2index[tri->vertex(CDT::cw (j))];
					cout << " " << v0 << " " << v1;
				}
			}
		}

		cout << endl;
	}
}
