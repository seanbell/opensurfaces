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

static void write_assignment(const std::string& output_filename,
								  const std::vector<int> labels) {
	
	std::cout << "Writing cluster centers to \""
			  << output_filename << "\"" << std::endl;

	std::ofstream wout(output_filename.c_str());
	if (wout.fail()) {
		std::cerr << "Failed to open \"" << output_filename
				  << "\" for writing." << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	wout << std::setprecision(1);
	for (unsigned int m=0; m < labels.size(); ++m) {
		wout << labels[m] << std::endl;
	}
	wout.close();

	return;
}


static int read_problem_data(const std::string& filename,
							  std::vector<std::vector<double> >& data) {
	data.clear();

	std::ifstream in(filename.c_str());
	if (in.fail()) {
		std::cerr << "Failed to open file \""
				  << filename << "\" for reading." << std::endl;
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
		data.push_back(current_data);
	}
	in.close();
	
	if (data.size() == 0) {
		std::cerr << "No points read from file \"" << filename
				  << "\"" << std::endl;
		std::cerr << "Try mpi_assign --help" << std::endl;
		exit(EXIT_FAILURE);
	}

	return(data.size());

}


int main(int argc, char* argv[]) {

	std::string data_filename;
	std::string cluster_filename;
	std::string assignment_filename;

	// Set Program options
	po::options_description generic("Generic Options");
	generic.add_options()
		("help","Produce help message")
		("verbose","Verbose output")
		;

	po::options_description input_options("Input/Output Options");
	input_options.add_options()
		("data",po::value<std::string>
		 (&data_filename)->default_value("data.txt"),
		 "Data file, one datum per line")
		("cluster",po::value<std::string>
		 (&cluster_filename)->default_value("clustercenter.txt"),
		 "Output file, one cluster center per line")
		("assignment",po::value<std::string>
		 (&assignment_filename)->default_value("assignment.txt"),
		 "Output file, one cluster center per line")
		;

	po::options_description all_options;
	all_options.add(generic).add(input_options);
	po::variables_map vm;
	po::store(po::command_line_parser(argc,argv).options(all_options).run(), vm);
	po::notify(vm);

	bool verbose = vm.count("verbose");

	if (vm.count("help")) {
		std::cerr << "Assigning points to cluster center" << std::endl;
		std::cerr << all_options << std::endl;
		std::cerr << std::endl;
		std::cerr << "Example:" << std::endl;
		std::cerr << "  mpi_assign --data example.txt --cluster clusters.txt --assignment assignment.txt" << std::endl;
		exit(EXIT_SUCCESS);
	}

	// read in the data
	std::cout << "Input file: " << data_filename << std::endl;
	std::vector<std::vector<double> > data_X;	
	int nof_points = read_problem_data(data_filename,data_X);
	assert(nof_points>0);


	// read in the clusters
	std::cout << "Clustercenter file: " << cluster_filename << std::endl;
	std::vector<std::vector<double> > data_CX;	
	int nof_clusters = read_problem_data(cluster_filename,data_CX);
	assert(nof_clusters>0);

	unsigned int dims = data_X[0].size();
	assert(dims>0);
	if (data_X[0].size() != data_CX[0].size()) {
		std::cerr << "Dimension mismatch between points and clusters" << std::endl;
		exit(EXIT_FAILURE);
	}

	// convert clusters to double*
	double *CX = (double *)malloc(nof_clusters * dims * sizeof(double));
	unsigned int cntr = 0;
	for (unsigned int m=0; m < data_CX.size() ; ++m) {
		for (unsigned int n=0; n < data_CX[m].size() ; ++n) {
			CX[cntr] = data_CX[m][n];
			cntr += 1;
		}
	}
	
	// start K-Means
	std::cout << "Starting Assignment ..." << std::endl;
	std::cout << " ... with " << nof_points << " training points " <<std::endl;
	std::cout << " ... for " << nof_clusters << " clusters " <<std::endl;
	std::cout << " ... in " << dims << " dimensions " <<std::endl;

	std::vector<int> labels;
	double *x = (double *)malloc(dims * sizeof(double));
	for (unsigned int i=0; i < nof_points ; i++ ) {
		for (unsigned int n=0; n<data_X[i].size() ; ++n)
			x[n] = data_X[i][n];
		labels.push_back(1+assign_point_to_cluster_ordinary(x,CX,dims,nof_clusters));
	}

	std::cout << "Done!" << std::endl;

	// write the clusters
	write_assignment(assignment_filename,labels);

	// done
	exit(EXIT_SUCCESS);
}
