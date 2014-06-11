#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <string>
#include <algorithm>
#include <iterator>
#include <numeric>
#include <ext/numeric>
#include <boost/program_options.hpp>
#include <boost/filesystem.hpp>

#include <stdlib.h>
#include <math.h>
#include <assert.h>

#include "mpi_kmeans.h"

namespace po = boost::program_options;

static unsigned int count_lines(const std::string& filename) {
	std::ifstream in(filename.c_str());
	if (in.fail()) {
		std::cerr << "count_lines, failed to open \"" << filename
			<< "\"." << std::endl;
		exit(EXIT_FAILURE);
	}
	unsigned int lines = 0;
	std::string line;
	while (in.eof() == false) {
		std::getline(in, line);
		if (line.size() == 0)
			continue;
		lines += 1;
	}
	in.close();
	return (lines);
}


static void write_cluster_centers(const std::string& output_filename,
								  const std::vector<std::vector<double> >& data_CX) {
	
	std::cout << "Writing cluster centers to \""
			  << output_filename << "\"" << std::endl;

	std::ofstream wout(output_filename.c_str());
	if (wout.fail()) {
		std::cerr << "Failed to open \"" << output_filename
				  << "\" for writing." << std::endl;
		exit(EXIT_FAILURE);
	}

	wout << std::setprecision(12);
	for (unsigned int m=0; m < data_CX.size(); ++m) {
		for (unsigned int n=0; n < data_CX[m].size(); ++n) {
			wout << (n==0? "":" ") << data_CX[m][n];
		}
		wout << std::endl;
	}
	wout.close();

	return;
}

static void write_cluster_centers(const std::string& output_filename,
								  double *data_CX, 
								  unsigned int nof_clusters,
								  unsigned int dims) {
	
	std::cout << "Writing cluster centers to \""
			  << output_filename << "\"" << std::endl;

	std::ofstream wout(output_filename.c_str());
	if (wout.fail()) {
		std::cerr << "Failed to open \"" << output_filename
				  << "\" for writing." << std::endl;
		exit(EXIT_FAILURE);
	}

	wout << std::setprecision(12);
	unsigned int cntr = 0;
	for (unsigned int m=0; m < nof_clusters; ++m) {
		for (unsigned int n=0; n < dims; ++n) {
			wout << (n==0? "":" ") << data_CX[cntr];
			cntr += 1;
		}
		wout << std::endl;
	}
	wout.close();

	return;
}


static int read_problem_data(const std::string& train_filename,
							  std::vector<std::vector<double> >& data_X) {
	data_X.clear();

	std::ifstream in(train_filename.c_str());
	if (in.fail()) {
		std::cerr << "Failed to open file \""
				  << train_filename << "\" for reading." << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	std::string line;
	unsigned int ndims = 0;
	while (in.eof() == false) {
		std::getline(in,line);
		if (line.size() == 0)
			continue; // skip over empty lines
	
		// remove trailing whitespaces 
		line.erase(line.find_last_not_of(" ")+1);

		std::vector<double> current_data;	
		std::istringstream is(line);
		while (is.eof() == false) {
			double value;
			is >> value;
			current_data.push_back(value);
		}
		
		// Ensure the same number of dimensions for each point
		if (ndims == 0)
			ndims = current_data.size();	
		assert(ndims == current_data.size());
		data_X.push_back(current_data);
	}
	in.close();
	
	if (data_X.size() == 0) {
		std::cerr << "No points read from file \"" << train_filename
				  << "\"" << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	return(data_X.size());

}

static int read_problem_data(const std::string& train_filename,
							  double *data_X) {

	std::ifstream in(train_filename.c_str());
	if (in.fail()) {
		std::cerr << "Failed to open file \""
				  << train_filename << "\" for reading." << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	unsigned int nof_points = count_lines(train_filename);
	if (nof_points == 0) {
		std::cerr << "No points read from file \"" << train_filename
				  << "\"" << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	std::string line;
	unsigned int ndims = 0;
	unsigned int cntr = 0;
	while (in.eof() == false) {
		std::getline(in,line);
		if (line.size() == 0)
			continue; // skip over empty lines
	
		// remove trailing whitespaces 
		line.erase(line.find_last_not_of(" ")+1);

		std::vector<double> current_data;	
		std::istringstream is(line);
		while (is.eof() == false) {
			double value;
			is >> value;
			current_data.push_back(value);
		}
		
		// Ensure the same number of dimensions for each point
		if (ndims == 0)
			ndims = current_data.size();	
		assert(ndims == current_data.size());
		if (data_X==NULL)
			data_X = (double *)malloc(nof_points * ndims * sizeof(double));
		
		for (unsigned int i=0; i<ndims; ++i) {
			data_X[cntr] = current_data[i];
			cntr += 1;
		}
	}
	in.close();
	
	return(nof_points);

}



int main(int argc, char* argv[]) {

	std::string train_filename;
	std::string weight_filename;
	std::string output_filename;
	int nof_clusters;
	int nof_restarts;
	int maxiter;

	// Set Program options
	po::options_description generic("Generic Options");
	generic.add_options()
		("help","Produce help message")
		("verbose","Verbose output")
		;

	po::options_description input_options("Input/Output Options");
	input_options.add_options()
		("data",po::value<std::string>
		 (&train_filename)->default_value("data.txt"),
		 "Training file, one datum per line")
		("output",po::value<std::string>
		 (&output_filename)->default_value("output.txt"),
		 "Output file, one cluster center per line")
		("weights",po::value<std::string>
		 (&weight_filename)->default_value(""),
		 "Weighting of exmaples, one number per line")
		;

	po::options_description kmeans_options("K-Means Options");
	kmeans_options.add_options()
		("k",po::value<int>(&nof_clusters)->default_value(100),
		 "Number of clusters to generate")
		("restarts",po::value<int>(&nof_restarts)->default_value(0),
		 "Number of K-Means restarts. (0: single run)")
		("maxiter",po::value<int>(&maxiter)->default_value(0),
		 "Maximum number of K-Means iterations. (0: infinity)")
		;

	po::options_description all_options;
	all_options.add(generic).add(input_options).add(kmeans_options);
	po::variables_map vm;
	po::store(po::command_line_parser(argc,argv).options(all_options).run(), vm);
	po::notify(vm);

	bool verbose = vm.count("verbose");

	if (vm.count("help")) {
		std::cerr << "K-Means clustering" << std::endl;
		std::cerr << all_options << std::endl;
		std::cerr << std::endl;
		std::cerr << "Example:" << std::endl;
		std::cerr << "  mpi_kmeans --k 2 --data example.txt --output clusters.txt" << std::endl;
		exit(EXIT_SUCCESS);
	}

	// read in the problem
	std::cout << "Training file: " << train_filename << std::endl;
	std::vector<std::vector<double> > data_X; // so far kmeans does not support std::<vector>
	int nof_points = read_problem_data(train_filename,data_X);
	assert(nof_points>0);

	unsigned int dims = data_X[0].size();
	assert(dims>0);

	// convert points to double*
	double *X = (double *)malloc(nof_points * dims * sizeof(double));
	unsigned int cntr = 0;
	for (unsigned int m=0; m < data_X.size() ; ++m) {
		for (unsigned int n=0; n < data_X[m].size() ; ++n) {
			X[cntr] = data_X[m][n];
			cntr += 1;
		}
		data_X[m].clear();
	}
	data_X.clear();



	// read in weighting
	double *W = NULL;
	if (weight_filename != "") {
		std::cout << "Weighting file: " << weight_filename << std::endl;
		std::vector<std::vector<double> > data_W; // so far kmeans does not support std::<vector>
		int nof_points_wfile = read_problem_data(weight_filename,data_W);
		assert(nof_points_wfile == nof_points);

		unsigned int dims_wfile = data_W[0].size();
		assert(dims_wfile==1);

		// convert points to double*
		W = (double *)malloc(nof_points * sizeof(double));
		for (unsigned int m=0; m < data_W.size() ; ++m)
			W[m] = data_W[m][0];
		data_W.clear();

	}

	// start K-Means
	std::cout << "Starting Kmeans ..." << std::endl;
	std::cout << " ... with " << nof_points << " training points " <<std::endl;
	std::cout << " ... for " << nof_clusters << " clusters " <<std::endl;

	unsigned int *assignment = (unsigned int *)malloc(nof_points * sizeof(unsigned int));
	double *CX = (double *) calloc(nof_clusters * dims, sizeof(double));
	double sse = kmeans(CX, X, W, assignment, dims, nof_points, nof_clusters, maxiter, nof_restarts);
	free(X); 
	assert(CX);

	std::cout << "Done!" << std::endl;
	std::cout << "Sum of Squared Error : " << sse << std::endl;

	// write the clusters
	// write_cluster_centers(output_filename,data_X);
	write_cluster_centers(output_filename,CX,nof_clusters,dims);

	// done
	exit(EXIT_SUCCESS);
}
