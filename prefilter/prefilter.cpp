#include "prefilter.h"

MTS_NAMESPACE_BEGIN

mat3 compute_homography(const vec2 *a, const vec2 *b, int n) {
	matX A = matX::Zero(n * 2, 9);
	for (int i = 0; i < n; ++i) {
		const float x = a[i][0], y = a[i][1];
		const float u = b[i][0], v = b[i][1];
		const int r1 = i * 2, r2 = r1 + 1;
		A(r1, 0) = -x;		A(r1, 1) = -y;		A(r1, 2) = -1;
		A(r1, 6) = u * x;	A(r1, 7) = u * y;	A(r1, 8) = u;
		A(r2, 3) = -x;		A(r2, 4) = -y;		A(r2, 5) = -1;
		A(r2, 6) = v * x;	A(r2, 7) = v * y;	A(r2, 8) = v;
	}

	vecX h = A.jacobiSvd(Eigen::ComputeFullV).matrixV().col(8);
	mat3 ret;
	ret << h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], h[8];
	return ret;
}

bool test_compute_homography() {
	cout << "compute_homography_test: ";
	for (int k = 0; k < 100; ++k) {
		float f = k / 200.0;
		float g = 1.0 - f;
		vec2 a[4] = { vec2(f, f),  vec2(g, f),  vec2(g, g),  vec2(f, g) };
		vec2 b[4] = { vec2(0, 0),  vec2(0.5, 0),  vec2(0.5, 1),  vec2(0, 1) };
		mat3 M = compute_homography(a, b);
		mat3 Minv = M.inverse();
		for (int i = 0; i < 4; ++i) {
			vec2 b_ = apply_homography(M, a[i]);
			vec2 a_ = apply_homography(Minv, b[i]);
			if (!approx_equals(b[i], b_) || !approx_equals(a[i], a_)) {
				cout << "FAIL" << endl;
				cout << "k:" << k << endl;
				cout << "M:" << M << endl;
				for (int j = 0; j < 4; ++j) {
					cout << "a[" << j << "]: " << a[j].transpose() << endl;
					cout << "b[" << j << "]: " << b[j].transpose() << endl;
				}
				cout << "a_[" << i << "]: " << a_.transpose() << endl;
				cout << "b_[" << i << "]: " << b_.transpose() << endl;
				return false;
			}
		}
	}
	cout << "PASS" << endl;
	return true;
}

HomographyEnvmap::HomographyEnvmap(ref<Bitmap> img_, float margin) :
		Emitter(Properties()), img(img_) {

	const float m1 = margin;
	const float m2 = 1.0 - margin;

	// +X left half of cube face
	vec2 a0[4] = { vec2(0, 0),  vec2(0.5, 0),  vec2(0.5, 1),  vec2(0, 1) };
	vec2 b0[4] = { vec2(m2, m1),  vec2(1, 0),  vec2(1, 1),  vec2(m2, m2) };

	// -X right half of cube face
	vec2 a1[4] = { vec2(0.5, 0),  vec2(1, 0),  vec2(1, 1),  vec2(0.5, 1) };
	vec2 b1[4] = { vec2(0, 0),  vec2(m1, m1),  vec2(m1, m2),  vec2(0, 1) };

	// +Y bottom half of cube face
	vec2 a2[4] = { vec2(0, 0),  vec2(1, 0),  vec2(1, 0.5),  vec2(0, 0.5) };
	vec2 b2[4] = { vec2(m1, m2),  vec2(m2, m2),  vec2(1, 1),  vec2(0, 1) };

	// -Y top half of cube face
	vec2 a3[4] = { vec2(0, 0.5),  vec2(1, 0.5),  vec2(1, 1),  vec2(0, 1) };
	vec2 b3[4] = { vec2(0, 0),  vec2(1, 0),  vec2(m2, m1),  vec2(m1, m1) };

	// -Z
	vec2 a4[4] = { vec2(0, 0),  vec2(1, 0),  vec2(1, 1),  vec2(0, 1) };
	vec2 b4[4] = { vec2(m1, m1),  vec2(m2, m1),  vec2(m2, m2),  vec2(m1, m2) };

	M[0] = compute_homography(a0, b0);
	M[1] = compute_homography(a1, b1);
	M[2] = compute_homography(a2, b2);
	M[3] = compute_homography(a3, b3);
	M[4] = compute_homography(a4, b4);
}

void test_HomographyEnvmap() {
	const std::string input = "../src/utils/prefilter/test.png" ;
	const float margin = 0.20;
	const int resolution = 512;

	ref<FileStream> in_file = new FileStream(input, FileStream::EReadOnly);
	ref<Bitmap> in_bitmap = new Bitmap(Bitmap::EAuto, in_file);
	in_bitmap->flipVertically();
	cout << "test_HomographyEnvmap: using " << in_bitmap->toString() << endl;

	HomographyEnvmap env(in_bitmap, margin);

    const float scale = 2.0 / resolution;
	std::vector<ref<Bitmap> > out_bitmaps;
    for (int k = 0; k < 6; ++k) {
    	out_bitmaps.push_back(ref<Bitmap>(new Bitmap(Bitmap::ERGB, Bitmap::EUInt8,
				Vector2i(resolution, resolution))));
    }

	for (int i = 0; i < resolution; ++i) { // row
		if (i % 10 == 0) {
			cout << "test_HomographyEnvmap: " << i << "/" << resolution << endl;
		}

		const float fv = scale * i - 1.0;
		for (int j = 0; j < resolution; ++j) { // column
			const float fu = scale * j - 1.0;

			const Vector3 v[6] = {
				normalize(Vector3(  1, fv,  fu)), // +X
				normalize(Vector3( -1, fv, -fu)), // -X
				normalize(Vector3( fu,  1,  fv)), // +Y
				normalize(Vector3( fu, -1, -fv)), // -Y
				normalize(Vector3(-fu, fv,   1)), // +Z
				normalize(Vector3( fu, fv,  -1))  // -Z
			};


			for (int k = 0; k < 6; ++k) {
				const Spectrum val = lookup_envmap(&env, v[k]);
				out_bitmaps[k]->setPixel(Point2i(j, i), val);
			}
		}
	}

	for (size_t i = 0; i < out_bitmaps.size(); ++i) {
		ref<FileStream> out_file = new FileStream("test_HomographyEnvmap" +
				boost::lexical_cast<string>(i) + ".jpg", FileStream::ETruncReadWrite);
		out_bitmaps[i]->flipVertically();
		out_bitmaps[i]->write(Bitmap::EJPEG, out_file);
	}
}


Bitmap* compute_prefiltered_envmap(const Emitter* envmap,
		const BSDF* bsdf, Sampler* sampler_parent,
		int resolution, int nsamples) {

	// each cube side is 2 units (-1 to +1)
    const float scale = 2.0 / resolution;

    Bitmap* ret = new Bitmap(Bitmap::ERGB,
    		Bitmap::EUInt8, Vector2i(resolution, resolution));

	#pragma omp parallel for schedule(dynamic, 4)
	for (int i = 0; i < resolution; ++i) {
		if (i % 32 == 0) {
			cout << "compute_prefiltered_cubemap: " << i << "/" << resolution << endl;
		}

		// each thread has its own sampler
		ref<Sampler> sampler = sampler_parent->clone();

		const float normal_y = scale * (i + 0.5) - 1.0;
		for (int j = 0; j < resolution; ++j) {
			const float normal_x = scale * (j + 0.5) - 1.0;

			Spectrum sum(0.0);
			int nsum = 0;

			float radius2 = normal_x * normal_x + normal_y * normal_y;
			if (radius2 <= 1) {
				const Vector3 normal = Vector3(normal_x, normal_y, sqrt(1 - radius2));

				Intersection its;
				its.shFrame = its.geoFrame = Frame(normal);
				its.p = Point3(0, 0, 0);
				its.uv = Point2(0, 0);
				its.wi = its.toLocal(Vector3(0, 0, 1)); // to camera

				sampler->generate(Point2i(i, j));
				for (int s = 0; s < nsamples; ++s) {
					// Compute bsdfWeight = f(wo, wi) / p(wo)
					BSDFSamplingRecord bRec(its, sampler, ERadiance);
					Spectrum bsdfWeight = bsdf->sample(bRec, sampler->next2D());
					if (!bsdfWeight.isZero() && bsdfWeight.isValid()) {
						sum += bsdfWeight * lookup_envmap(envmap,
								normalize(its.toWorld(bRec.wo)));
						nsum ++;
					}
					sampler->advance();
				}
			}

			ret->setPixel(Point2i(j, i),
					(nsum > 0) ? (sum / nsum) : Spectrum(0.0));
		}
	}

	return ret;
}

int Prefilter::run(int argc, char **argv) {

	////
	// PARSE ARGS

	vector<string> args;
	for (int i = 0; i < argc; ++i) {
		args.push_back(string(argv[i]));
	}

	if (args.size() == 2 && args[1] == "--test") {
		test_compute_homography();
		test_HomographyEnvmap();
		return 0;
	}

	if (args.size() < 4) {
		cout << "Usage: " << args[0] << " scene.xml bsdf_name out.png" << endl;
		return 1;
	}

	string scene_path = args[1];
	string scene_bsdf_path = args[2];
	string out_path = args[3];

	cout << "Arguments:" << endl
	     << "    scene_path: " << scene_path << endl
	     << "    scene_bsdf_path: " << scene_bsdf_path << endl
	     << "    out_path: " << out_path << endl;

	ref<Scene> scene = loadScene(scene_path, ParameterMap());
	if (!scene) Log(EError, "No scene");
    cout << "Scene: " << scene->toString() << endl;

	Sampler* sampler = scene->getSampler();
	if (!sampler) Log(EError, "No sampler");

	const Emitter* envmap = scene->getEnvironmentEmitter();
	if (!envmap) Log(EError, "No envmap");
	if (!scene->getSensor()) Log(EError, "No sensor");
	if (!scene->getSensor()->getFilm()) Log(EError, "No sensor film");
	int resolution = scene->getSensor()->getFilm()->getSize()[0];
	int nsamples = sampler->getSampleCount();

	ref<Scene> scene_bsdf = loadScene(scene_bsdf_path, ParameterMap());
	if (!scene_bsdf) Log(EError, "No bsdf scene");
	scene_bsdf->initialize();
    cout << "BSDF Scene: " << scene->toString() << endl;
	BSDF* bsdf = NULL;
	ref_vector<ConfigurableObject> objs = scene_bsdf->getReferencedObjects();
	for (size_t i = 0; i < objs.size(); ++i) {
		if (objs[i] && objs[i]->getClass()->derivesFrom(MTS_CLASS(BSDF))) {
			bsdf = static_cast<BSDF*>(objs[i].get());
		}
	}
	if (!bsdf) Log(EError, "No bsdf");

    cout << "BSDF: " << bsdf->toString() << endl;
    cout << "Envmap: " << envmap->toString() << endl;
    cout << "Sampler: " << sampler->toString() << endl;
    cout << "Resolution: " << resolution << endl;
    cout << "Sample Count: " << nsamples << endl;

	ref<Bitmap> out_bitmap = compute_prefiltered_envmap(envmap,
			bsdf, sampler, resolution, nsamples);

	cout << "Saving: " << out_path << endl;
	ref<FileStream> out_file = new FileStream(out_path, FileStream::ETruncReadWrite);
	out_bitmap->flipVertically();
	out_bitmap->write(Bitmap::EPNG, out_file);

	//cout << "Computing diffuse matrix" << endl;
	//cout << mat4s_to_glsl_string(compute_sh9_diffuse_matrix(
	//		homography_envmap, sampler, nsamples * resolution * resolution)) << endl;

	return 0;
}

MTS_EXPORT_UTILITY(Prefilter, "Prefilter an image into an environment map")
MTS_NAMESPACE_END
