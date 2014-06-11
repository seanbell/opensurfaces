#include <mitsuba/core/plugin.h>
#include <mitsuba/core/bitmap.h>
#include <mitsuba/core/fstream.h>
#include <mitsuba/render/util.h>
#include <boost/lexical_cast.hpp>

MTS_NAMESPACE_BEGIN

/* RGBE encoding, code borrowed from bitmap.cpp */
inline void rgb_to_rgbe(float *rgb, uint8_t rgbe[4]) {
	/* Find the largest contribution */
	Float max = std::max(std::max(rgb[0], rgb[1]), rgb[2]);
	if (max < 1e-32) {
		rgbe[0] = rgbe[1] = rgbe[2] = rgbe[3] = 0;
	} else {
		int e;
		/* Extract exponent and convert the fractional part into
		   the [0..255] range. Afterwards, divide by max so that
		   any color component multiplied by the result will be in [0,255] */
		max = std::frexp(max, &e) * (Float) 256 / max;
		rgbe[0] = (uint8_t) (rgb[0] * max);
		rgbe[1] = (uint8_t) (rgb[1] * max);
		rgbe[2] = (uint8_t) (rgb[2] * max);
		rgbe[3] = e+128; /* Exponent value in bias format */
	}
}

/* RGB + scale encoding (i.e. rgb = s * (r, g, b)) */
inline void rgb_to_rgbs(float *rgb, uint8_t rgbs[4]) {
	/* Find the largest contribution */
	Float max = std::max(std::max(rgb[0], rgb[1]), rgb[2]);
	if (max < 1e-32) {
		rgbs[0] = rgbs[1] = rgbs[2] = rgbs[3] = 0;
	} else {
		rgbs[0] = (uint8_t) (rgb[0] * 255 / max);
		rgbs[1] = (uint8_t) (rgb[1] * 255 / max);
		rgbs[2] = (uint8_t) (rgb[2] * 255 / max);
		rgbs[3] = (uint8_t) (clamp<Float>(max, 0, 255));
	}
}

class EncodeHDR : public Utility {
public:
	int run(int argc, char **argv) {
		if (argc < 7) {
			cout << "Take images and convert them to RGBE format encoded as RGBA png," << endl
				 << "while also stacking them together into a grid of size rows x cols" << endl;
			cout << "Syntax: mtsutil encodehdr <rgbe|rgbs> <rows> <cols> <scale>" << endl
				 << "                          <img1.exr> [<img2.exr> ...] out.png" << endl;
			return 1;
		}

		ref_vector<Bitmap> bitmaps;
		ref<FileStream> out_file = new FileStream(
				argv[argc - 1], FileStream::ETruncReadWrite);

		std::string encoding = argv[1];
		int nrows = boost::lexical_cast<int>(argv[2]);
		int ncols = boost::lexical_cast<int>(argv[3]);
		float scale = boost::lexical_cast<float>(argv[4]);

		// use a function pointer to split between the two methods
		void (*encode_method)(float*, uint8_t*) = NULL;
		if (encoding == "rgbe") {
			encode_method = &rgb_to_rgbe;
		} else if (encoding == "rgbs") {
			encode_method = &rgb_to_rgbs;
		} else {
			cout << "Unknown encoding method: " << encoding << endl;
			return 1;
		}

		int max_width = 0, max_height = 0;
		for (int i = 5; i < argc - 1; ++i) {
			ref<FileStream> file   = new FileStream(argv[i], FileStream::EReadOnly);
			ref<Bitmap> bmp = new Bitmap(Bitmap::EAuto, file);
			max_width = std::max(max_width, bmp->getHeight());
			max_height = std::max(max_height, bmp->getHeight());
			bitmaps.push_back(bmp->convert(Bitmap::ERGB, Bitmap::EFloat32, 1.0, scale));
		}

		int out_width = max_width * ncols;
		int out_height = max_height * nrows;

		ref<Bitmap> out_bmp = new Bitmap(Bitmap::ERGBA,
				Bitmap::EUInt8, Vector2i(out_width, out_height));

		// also compute a histogram of the 4th channel (E or S)
		std::vector<int> histogram(256, 0);

		for (size_t i = 0; i < bitmaps.size(); ++i) {
			int row = i / nrows;
			int col = i % nrows;
			size_t x_off = col * max_width;
			size_t y_off = row * max_height;

			Bitmap *bi = bitmaps[i];
			float* bi_data = bi->getFloat32Data();
			int bi_height = bi->getHeight();
			int bi_width = bi->getWidth();

			for (int y = 0; y < bi_height; ++y) {
				uint8_t* out_data = out_bmp->getUInt8Data() + ((x_off + (y + y_off) * out_width) * 4);

				for (int x = 0; x < bi_width; ++x) {
					uint8_t encoded[4];
					(*encode_method)(bi_data, encoded);
					*out_data++ = encoded[0];
					*out_data++ = encoded[1];
					*out_data++ = encoded[2];
					*out_data++ = encoded[3];
					histogram[encoded[3]] ++;
					bi_data += 3;
				}
			}
		}

		out_bmp->write(Bitmap::EPNG, out_file);

		cout << "4th channel histogram:" << endl;
		for (int i = 0; i < 256; ++i) {
			if (histogram[i] > 0)
				cout << i << "\t" << histogram[i] << endl;
		}

		return 0;
	}

	MTS_DECLARE_UTILITY()
};

MTS_EXPORT_UTILITY(EncodeHDR, "Pack HDR images into one LDR encoded image")
MTS_NAMESPACE_END
