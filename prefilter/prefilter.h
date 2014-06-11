#pragma once
#if !defined(__PREFILTER_H)
#define __PREFILTER_H

#include <mitsuba/core/plugin.h>
#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/fstream.h>
#include <mitsuba/render/util.h>
#include <mitsuba/render/bsdf.h>
#include <mitsuba/render/sampler.h>
#include <boost/lexical_cast.hpp>
#include <Eigen/Dense>
#include <vector>
#include <string>


/**
 * NOTE ABOUT CUBEMAP COORDINATE SYSTEMS:
 *
 * This code uses a right-handed system everywhere (X right, Y up, -Z forward).
 *
 * There are some serious sign issues with cube maps in general.  Within this code
 * base, the cube assumes a right-handed system where each cube face is, starting
 * from looking down -Z with +X right and +Y up:
 *    +X: turn right 90 degrees
 *    -X: turn left 90 degrees
 *    +Y: turn up 90 degrees
 *    -Y: turn down 90 degrees
 *    +Z: turn around 180 degrees about Y
 *    -Z: no change
 *
 * HOWEVER, OpenGL seems to have a left-handed system for cube maps with +Z forward
 * and  with Y inverted (pointing down).  Further, libraries that wrap OpenGL
 * (e.g. three.js) seem to flip things around even more, sometimes inconsistently.
 * Therefore, I am going to work within the above right-handed system for this code
 * base, and worry about translating to a particular rendering library separately.
 */


MTS_NAMESPACE_BEGIN

typedef Eigen::Matrix<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> matX;
typedef Eigen::Matrix<int, Eigen::Dynamic, Eigen::Dynamic, Eigen::ColMajor> matXi;
typedef Eigen::Matrix<float, Eigen::Dynamic, 1, Eigen::ColMajor> vecX;
typedef Eigen::Matrix<float, 3, 3, Eigen::ColMajor> mat3;
typedef Eigen::Matrix<float, 4, 4, Eigen::ColMajor> mat4;
typedef Eigen::Matrix<Spectrum, 4, 4, Eigen::ColMajor> mat4s;
typedef Eigen::Matrix<float, 2, 1, Eigen::ColMajor> vec2;
typedef Eigen::Matrix<float, 3, 1, Eigen::ColMajor> vec3;
typedef Eigen::Array<float, 9, 1, Eigen::ColMajor> arr9;
typedef Eigen::Array<Spectrum, 9, 1, Eigen::ColMajor> arr9s;
typedef Eigen::Array<float, 3, 1, Eigen::ColMajor> arr3;
typedef Eigen::AlignedBox<int, 2> ibbox2;
typedef Eigen::Matrix<int, 2, 1> ivec2;

using std::vector;
using std::string;
using std::abs;

enum ECubeSide { POSX, NEGX, POSY, NEGY, POSZ, NEGZ };

/**
 * Returns true if two vectors are approximately equal
 */
template <typename A, typename B>
inline bool approx_equals(A a , B b, float epsilon = 1e-5) {
	if (a.size() != b.size()) return false;
	for (int i = 0; i < a.size(); ++i) {
		if (abs(a.coeff(i) - b.coeff(i)) > epsilon) {
			return false;
		}
	}
	return true;
}

/**
 * Compute the homography between mappings of points a --> b, returning M such that
 *     <constant> * [ b' 1 ]' = M * [ a' 1 ]'
 */
mat3 compute_homography(const vec2 *a, const vec2 *b, int n = 4);
bool test_compute_homography();

/**
 * Applies a homography and projects back to cartesian coordinates
 */
inline vec2 apply_homography(const mat3& M, const vec2& a) {
	vec3 b = M * vec3(a[0], a[1], 1.0);
	return vec2(b[0] / b[2], b[1] / b[2]);
}

/**
 * Wrapper around envmap lookup
 */
template <typename V3>
inline Spectrum lookup_envmap(const Emitter* env, const V3& v) {
	return env->evalEnvironment(RayDifferential(
			Point3(0,0,0), Vector3(v[0], v[1], v[2]), 0.0));
}

/**
 * Converts a single image into an entire cube map as follows:
 *
 *          /-------------------\   ^
 *          | \      +Y       / |   | margin * height
 *          |  ---------------  |   v
 *          |  |             |  |
 *          |-X|     -Z      |+X|
 *          |  |             |  |
 *          |  ---------------  |   ^
 *          | /      -Y       \ |   | margin * height
 *          \-------------------/   v
 *          <--> margin * width
 *                           <--> margin * width
 */
class HomographyEnvmap : public Emitter {
public:
	HomographyEnvmap(ref<Bitmap> img_, float margin_);

	HomographyEnvmap(Stream *stream, InstanceManager *manager) : Emitter(stream, manager) {
		Log(EError, "TODO");
	}

	inline Spectrum evalEnvironment(const RayDifferential& ray) const {
		const Vector3& v = ray.d;
		int idx;
		arr3(v[0], v[1], v[2]).abs().maxCoeff(&idx);
		const float x = v[0], y = v[1], z = v[2];
		vec2 uv;
		switch (idx) {
			case 0:
				if (x > 0) { // +X
					// map right half of cubeface to left half of image
					uv = apply_homography(M[0], vec2(
							0.5 * (-abs(z) / x) + 0.5,
							0.5 * (y / x) + 0.5)  );
				} else { // -X
					// map left half of cubeface to right half of image
					uv = apply_homography(M[1], vec2(
							0.5 * (abs(z) / (-x)) + 0.5,
							0.5 * (y / (-x)) + 0.5)  );
				}

				break;

			case 1:
				if (y > 0) { // +Y
					uv = apply_homography(M[2], vec2( // map to bottom half
							0.5 * (x / y) + 0.5,
							0.5 * (-abs(z) / y) + 0.5)  );
				} else { // -Y
					uv = apply_homography(M[3], vec2( // map to top half
							0.5 * (x / (-y)) + 0.5,
							0.5 * (abs(z) / (-y)) + 0.5) );
				}
				break;

			case 2: // +/- Z
				uv = apply_homography(M[4], vec2( // map to entire square
						0.5 * (x / abs(z)) + 0.5,
						0.5 * (y / abs(z)) + 0.5) );
				break;
		}

		// fetch pixel, clamping to edge
		return img->getPixel(Point2i(
				clamp<int>(uv[0] * img->getWidth(), 0, img->getWidth() - 1),
			    clamp<int>(uv[1] * img->getHeight(), 0, img->getHeight() - 1)));
	}

	AABB getAABB() const {
		return AABB(Point(0,0,0));
	}


private:
	mat3 M[5]; // +X, -X, +Y, -Y, +/- Z
	ref<Bitmap> img;
};

/**
 * Functional test for HomographyEnvmap -- outputs images into current directory
 */
void test_HomographyEnvmap();

/**
 * Computes the cubemap, assuming OpenGL ordering
 * (+X, -X, +Y, -Y, +Z, -Z, each side row-major with 0th row at bottom)
 *
 *
 */
Bitmap* compute_prefiltered_envmap(const Emitter* envmap,
		const BSDF* bsdf, Sampler* sampler,
		int resolution, int samples);


/**
 * Projects a 3D cartesian vector into the first 9 SH coefficients
 */
template <typename V3>
inline arr9 cartesian_to_sh9(const V3 &x) {
	arr9 sh;
	sh[0] = 0.2820947917738781434740397257804;
	sh[1] = 0.4886025119029199215863846228384 * x[1];
	sh[2] = 0.4886025119029199215863846228384 * x[2];
	sh[3] = 0.4886025119029199215863846228384 * x[0];
	sh[4] = 1.0925484305920790705433857058027 * x[1] * x[0];
	sh[5] = 1.0925484305920790705433857058027 * x[1] * x[2];
	sh[6] = 1.0925484305920790705433857058027 * x[2] * x[0];
	sh[7] = 0.3153915652525200060308936902957 * (3 * x[2] * x[2] - 1);
	sh[8] = 0.5462742152960395352716928529014 * (x[0] * x[1] - x[1] * x[1]);
	return sh;
}

/**
 * Computes the first 9 spherical harmonics for an environment map
 */
inline arr9s compute_sh9(const HomographyEnvmap* envmap,
		ref<Sampler> sampler_parent, int nsamples) {
	arr9s ret = arr9s::Constant(Spectrum(0.0));

	#pragma omp parallel for schedule(dynamic, 1)
	for (int k = 0; k < 128; ++k) {
		arr9s sum = arr9s::Constant(Spectrum(0.0));

		// each thread has its own sampler
		ref<Sampler> sampler = sampler_parent->clone();
		sampler->generate(Point2i(k, 0));
		for (int i = 0; i < nsamples; ++i)	{
			const Vector3 v = Warp::squareToUniformSphere(sampler->next2D());
			const arr9 sh9 = cartesian_to_sh9(v);
			const Spectrum L = lookup_envmap(envmap, v);
			for (int j = 0; j < 9; ++j)
				ret[j] += sh9[j] * L;
			sampler->advance();
		}

		#pragma omp critical
		{
			sum += ret;
		}
	}

	// sampling by solid angle: p(direction) = 1 / 4pi
	float scale = 4.0 * M_PI / nsamples;
	for (int j = 0; j < 9; ++j)
		ret[j] *= scale;
	return ret;
}

/**
 * Computes the 4x4 matrix used for diffuse lighting
 * Uses method from [ Ravi Ramamoorthi and Pat Hanrahan, "An Efﬁcient
 * Representation for Irradiance Environment Maps", SIGGRAPH 2001.
 * http://graphics.stanford.edu/papers/envmap/envmap.pdf ]
 */
inline mat4s compute_sh9_diffuse_matrix(const HomographyEnvmap* envmap,
		ref<Sampler> sampler, int nsamples) {
	mat4s ret;
	arr9s sh9 = compute_sh9(envmap, sampler, nsamples);
	const float c1 = 0.429043, c2 = 0.511664, c3 = 0.743125, c4 = 0.886227, c5 = 0.247708;
	ret << c1 * sh9[8],  c1 * sh9[4], c1 * sh9[7], c2 * sh9[3],
		   c1 * sh9[4], -c1 * sh9[8], c1 * sh9[5], c2 * sh9[1],
		   c1 * sh9[7],  c1 * sh9[5], c3 * sh9[6], c2 * sh9[2],
		   c2 * sh9[3],  c2 * sh9[1], c2 * sh9[2], c4 * sh9[0] - c5 * sh9[6];
	return ret;
}

inline std::string mat4s_to_glsl_string(const mat4s& m) {
	std::stringstream ss;
	ss.precision(8);
	const char names[3] = {'r', 'g', 'b'};
	for (int c = 0; c < 3; ++c) {
		ss << "mat4 M" << names[c] << "=mat4(";
		for (int i = 0; i < 4; ++i) {
			ss << ((i > 0) ? ",vec4(" : "vec4(");
			for (int j = 0; j < 4; ++j) {
				if (j > 0) ss << ",";
				float rgb[3];
				// NOTE THE TRANSPOSE -- each vec4 is a column
				m(j, i).toLinearRGB(rgb[0], rgb[1], rgb[2]);
				ss << rgb[c];
			}
			ss << ")";
		}
		ss << ");" << endl;
	}
	return ss.str();
}


class Prefilter : public Utility {
public:

	int run(int argc, char **argv);
	MTS_DECLARE_UTILITY()
};

MTS_NAMESPACE_END
#endif
