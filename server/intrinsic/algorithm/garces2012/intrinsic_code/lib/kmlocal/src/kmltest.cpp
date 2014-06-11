//----------------------------------------------------------------------
//	File:		kmltest.cc
//	Programmer:	David Mount
//	Last modified:	08/07/05
//	Description:	test/evaluation driver for kMeans
//----------------------------------------------------------------------
// Copyright (C) 2004-2005 David M. Mount and University of Maryland
// All Rights Reserved.
// 
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation; either version 2 of the License, or (at
// your option) any later version.  See the file Copyright.txt in the
// main directory.
// 
// The University of Maryland and the authors make no representations
// about the suitability or fitness of this software for any purpose.
// It is provided "as is" without express or implied warranty.
//----------------------------------------------------------------------

#include <iostream>			// file I/O
#include <string.h>			// string ops
#include <ctime>			// clock
#include <cmath>			// math routines

#include "KMeans.h"			// k-means includes
#include "KMterm.h"			// k-means termination
#include "KMdata.h"			// data point set
#include "KMfilterCenters.h"		// center point set (for filtering)
#include "KMlocal.h"			// k-means algorithms
#include "KMrand.h"			// random point generation

//----------------------------------------------------------------------
// kmltest
//
// This program is a driver for testing and evaluating various algorithms
// for the k-means problem, for point clustering in multi-dimensional
// spaces.  It allows the user to generate or input data sets, to specify
// the number of centers and generate or input their initial positions,
// and then to run one of a number of k-means procedures.
//
// Overview:
// ---------
// The test program is run as follows:
// 
// 	kmltest < test_input > test_output
//
// where the test_input file contains a list of directives as described
// below.  Directives consist of a directive name, followed by list of
// arguments (depending on the directive).  Arguments and directives are
// separated by white space (blank, tab, and newline).  String arguments
// are not quoted, and consist of a string of nonwhite chacters.  A
// character "#" denotes a comment.  The following characters up to
// the end of line are ignored.  Comments may only be inserted between
// directives (not within the argument list of a directive).
//
// Algorithm Overview:
// -------------------
// The generic algorithm begins by generating an initial solution curr
// and saving it in best.  These objects are local to the KMlocal
// structure.   The value of curr reflects the current solution and
// best reflects the best solution seen so far.
//
// The generic algorithm consists of some number of basic iterations,
// called stages.  Each stage involves the execution of one step of
// either the swap heuristic or Lloyd's algorithm.  Each of the
// algorithms differ in how they apply these stages.
//
// Stages are grouped into runs.  Intuitively, a run involves a
// (small) number of stages in search of a better solution.  A run might
// end, say, because a better solution was found or a fixed number of
// stages have been performed without any improvement. 
//
// After a run is finished, we check to see whether we want to accept
// the solution.  Presumably this happens if the cost is lower, but it
// may happen even if the cost is inferior in other circumstances (e.g.,
// as part of a simulated annealing approach).  Accepting a solution
// means copying the current solution to the saved solution.  In some
// cases, the acceptance may involve reseting the current solution to a
// random solution.
//
// Algorithm Details:
// ------------------
// There are some concepts that are important to run/phase transitions.
// One is the maximum number of stages.  Most algorithms provide some
// sort of parameter that limits the number of stages that the algorithm
// can spend in a particular run (before giving up).  The second is the
// relative distortion loss, or RDL. (See also KMterm.h.) The RDL is
// defined:
//
//		initDistortion - currDistortion
//       RDL =  -------------------------------
//                    initDistortion
//
// Note that a positive value indicates that the distortion has
// decreased.  The definition of "initDistortion" depends on the
// algorithm.  It may be the distortion of the previous stage (RDL =
// consecutive RDL), or it may be the distortion at the beginning of the
// run (RDL = accumulated RDL).
//
// Here is a more detailed explanation of the algorithms.
//
// KMlocalLloyds
// -------------
//	This is Lloyd's algorithm with random restarts The algorithm is
//	broken into phases, and each phase is broken into runs.  Each
//	phase starts by sampling center points at random.  Each run is
//	provided two parameters, a maximum number of runs per stage
//	(max_run_stage) and a minimum accumulated relative distortion
//	loss (min_accum_rdl).  If the accumulated RDL for the run
//	exceeds this value, then the run ends in success.  If the number
//	of stages is exceeded before this happens, the run ends in
//	failure.  The phase ends with the first failed run.
// KMlocalSwap
// -----------
//	This algorithm iteratively changes centers by performing swaps.
//	Each run consists of a given number (max_swaps) executions of
//	the swap heuristic.
// KMlocalEZ_Hybrid
// ----------------
//	This implements a simple hybrid algorithm (compared to
//	KMlocalHybrid).  The algorithm performs only one swap, followed
//	by some number of iterations of Lloyd's algorithm.  Lloyd's
//	algorithm is repeated until the consecutive RDL falls below a
//	given threshold.
//
//	A stage constitutes one invocation of the Swap or Lloyd's
//	algorithm.  A run consists of a single swap followed by a
//	consecutive sequence of Lloyd's steps.  A graphical
//	representation of one run is presented below.  The decision to
//	make another pass through Lloyd's is based on whether the
//	relative improvement since the last stage (consecutive relative
//	distortion loss) is above a certain fixed threshold
//	(min_consec_rdl).
// KMlocalHybrid
// -------------
//	This implements a more complex hybrid algorithm, which combines
//	both of swapping and Lloyd's algorithm with a variant of
//	simulated annealing.  The algorithm's execution is broken into
//	the following different processes: one swap, a consecutive
//	sequence of Lloyd's steps, and an acceptance test.  If we pass
//	the acceptance test, we take the resulting solution, and
//	otherwise we restore the old solution.
//
//	The decision to perform another Lloyd's step or go on to
//	acceptance is based on whether the relative improvement since
//	the last stage (consecutive relative distortion loss) is above a
//	certain fixed threshold (min_consec_rdl).
//
//	If the resulting solution is better than the saved solution,
//	then we accept it.  Otherwise, we use the simulated annealing
//	decision choice (described below) to decide whether to accept
//	it.
//
//	Simulated Annealing Choice
//	--------------------------
//	The choice to accept a poorer solution occurs with probability
//
//		exp(RDL/T),
//
//	where RDL is the relative distortion loss (relative to the
//	saved solution), and T is the current temperature.  Note that
//	if RDL > 0 (improvement) then this quantity is > 1, and so we
//	always accept.
//
//	The temperature value T is a decreasing function of the number
//	of the number of stages.  It starts at some initial value T0 and
//	decreases slowly over time.  Rather than using the standard (slow)
//	Boltzman annealing schedule, we use the following fast annealing
//	schedule, every L stages we set
//
//		T = TF * T,
//
//	where:
//		L (= temp_run_length) is an integer parameter set by the
//		    user.  (Presumably it depends on the number of
//		    centers and the dimension of the space.)
//		TF (= temp_reduc_factor) is a real number of the form 1-x,
//		    for some small x.
//
//	The initial temperature T0 is a tricky thing to set.  The user
//	supplies a parameter p0 = init_prob_accept, the initial
//	probability of accepting a random swap.  However, the
//	probability of acceting a swap depends on the given RDL value.
//	To estimate this, for the first L runs we use p0 as the
//	probability.  Over these runs we compute the average rdl value.
//	Once the first L runs have completed, we set T0 so that:
//
//		exp(-averageRDL/T0) = initProbAccept,
//
//	or equivalently
//
//		T0 = -averageRDL/(ln initProbAccept).
//
// Basic operations:
// -----------------
// The test program can perform the following operations.  How these
// operations are performed depends on the options which are described
// later. 
//
//	Data Generation:
//	----------------
//	read_data_pts <file>	Create a set of data points whose
//				coordinates are input from file <file>.
//				Prior to this, data_size must be set.
//				At most data_size points will be read
//				from the file.  The actual number of
//				points in the file may be less.
//	gen_data_pts		Create a set of data points whose
//				coordinates are generated from the
//				current point distribution.
//
//	Running k-means:
//	----------------
//	run_kmeans <string>	Apply k-means clustering to the current
//				point set and clusters.  The string
//				specifies the desired version of k-means.
//				These include:
//				    lloyd = runs Lloyd's algorithm using
//					    the filtering algorithm.
//				    swap  = runs the swap heuristic.
//				    hybrid = runs Lloyd's algorithm
//					    and the swap heuristic in
//					    alternating steps.
//				    EZ-hybrid = a simpler version of
//					    hybrid. One swap followed
//					    by some number of Lloyd's.
//
//	Miscellaneous: (Strings may have no embedded blanks.)
//	-----------------------------------------------------
//	title <string>		Experiment title.
//	print <string>		Output string to console (cerr).
//	get_distortion		Computes and prints distortion (the sum
//				of squared distances for the current
//				centers).  Note that the kmeans algorithms
//				compute and print the distortion for all
//				stages but stage 0, if the stats level
//				is set to stage.
//
// Options:
// --------
// How these operations are performed depends on a set of options.
// If an option is not specified, a default value is used. An option
// retains its value until it is set again.  String inputs are not
// enclosed in quotes, and must contain no embedded white space (sorry,
// this is C++'s convention).
//
// Options affecting data and query point generation:
// --------------------------------------------------
//	kcenters <int>		Number of centers.  Default = 5.
//	dim <int>		Dimension of space.
//	seed <int>		Seed for random number generation.
//	data_size <int>		Number of data points to generate for
//				gen_data_pts points and the maximum
//				number of data points to be read for
//				read_data_pts.  If this exceeds
//				max_data_size, then max_data_size is
//				incremented to match this value.
//				Default = 100.
//	std_dev <float>		Standard deviation (used in gauss, and
//				clustered distributions).  This is the
//				"small" distribution for clus_ellipsoids.
//				Default = 1.
//	std_dev_lo <float>	Low and high standard deviations (used in
//	std_dev_hi <float>	clus_ellipsoids).  Default = 1.
//	corr_coef <float>	Correlation coefficient (used in co-gauss
//				and co_lapace distributions). Default = 0.05.
//	colors <int>		Number of color classes (clusters) (used
//				in the clustered distributions).  Def. = 5.
//	new_clust		Once generated, cluster centers are not
//				normally regenerated.  This is so that both
//				centers and data points can be generated
//				using the same set of clusters.  This option
//				forces new cluster centers to be generated
//				with the next generation of either data or
//				center points.
//	max_clus_dim <int>	Maximum dimension of clusters (used in
//				clus_orth_flats and clus_ellipsoids).
//				Default = 1.
//	distribution <string>	Type of input distribution
//				    uniform	= uniform over cube [-1,1]^d.
//				    gauss	= Gaussian with mean 0
//				    laplace	= Laplacian, mean 0 and var 1
//				    co_gauss	= correlated Gaussian
//				    co_laplace	= correlated Laplacian
//				    clus_gauss	= clustered Gaussian
//				    clus_orth_flats = clusters of orth flats
//				    clus_ellipsoids = clusters of ellipsoids
//				    multi_clus  = multi-sized clusters
//				See the file rand.cc for further information.
//
// Options affection general program behavior:
// -------------------------------------------
//	stats <string>		Level of statistics output
//				    silent	 = no output,
//				    exec_time	+= execution time only
//				    summary	+= summary of complete kmeans
//				    stage	+= summary of each stage
//				    step	+= show each step
//				    centers	+= print centers each time
//				    tree	+= show the tree.
//				Default = "summary".
//	print_points <string>	Print points after reading/generating?
//				Argument is either "yes" or "no".
//				Default = "no".
//	show_assignments <string>
//				Print the indices of the center to
//				which each point has been assigned along
//				with its distance to this center, after
//				the algorithm terminates.  Argument is
//				either "yes" or "no".
//				Default = "no".
//	validate <string>	Test (through a slow brute-force search)
//				that the center assignments requested by
//				show_assignments is correct.  This is
//				used for debugging, and will slow
//				overall execution.  Argument is either
//				"yes" or "no".
//				Default = "no".
//				(Note: There are other elements of the
//				computation that could be validated.
//				Perhaps with time these will be included
//				under this option.)
//
// Options affecting termination:
// ------------------------------
// The way of controlling the program's termination is to specify the
// maximum number of stages.  (In theory, a better way would be to
// determine when the algorithm has converged, but this seems to be a
// very complex task to me.)  Each time the algorithm moves the center
// points and recomputes the distortion constitutes a stage.  The
// maximum number of stages is based on the number of data points n
// (data_size) and the number of centers k (kcenters) and four
// coefficients, a,...,d, using the following formula:
//
//	MAX_STAGE = a + (b*k + c*n)^d
//
// In addition there are the following parameters.  They are based
// on the "relative distortion loss" (RDL), which is defined to be
// the relative decrease in the distortion.
//
//	max_tot_stage 4*<float>
//				Maximum total stages given as paramters
//				(a,...,d).
//				Default: 0,0,0,0.
//
// Options affecting algorithm execution:
// --------------------------------------
//
//   Options used in Lloyd's Algorithm and Hybrid Algorithms:
//   --------------------------------------------------------
//	damp_factor <float>	A dampening factor in the interval
//				(0,1].  The value 1 is the standard
//				Lloyd's algorithm.  Othewise, each point
//				is only moved by this fraction of the
//				way from its current location to the
//				centroid.  Default: 1
//	min_accum_rdl <float>	This is used in Lloyd's algorithm
//				algorithm which perform multiple swaps.
//				When performing p swaps, we actually may
//				perform fewer than p.  We stop
//				performing swaps, whenever the total
//				distortion (from the start of the run)
//				has decreased by at least this amount.
//				Default: 0.10
//	max_run_stage <int>	This is used in Lloyd's algorithm.  A
//				run terminates after this many stages.
//				Default: 100
//
//   Options specific to the swap algorithm:
//   ---------------------------------------
//	max_swaps <int>		Maximum swaps at any given stage.
//				Default: 1
//
//   Options specific to the hybrid algorithms:
//   ------------------------------------------
//	min_consec_rdl <float>	This is used in the hybrid algorithms.
//				If the RDL of two consecutive runs is
//				less than this value Lloyd's algorithm
//				is deemed to have converged, and the run
//				ends.
//   Options specific to the (complex) hybrid algorithm:
//   ---------------------------------------------------
//	init_prob_accept <float> The initial probability of accepting a
//				solution that does not improve the
//				distortion.
//	temp_run_length <int>	The number of stages before chaning the
//				temperature.
//	temp_reduc_factor <float> The factor by which temperature is
//				reduced at the end of a temperature run.
//
//  Example:
//  --------
//    title Experiment_1A		# experiment title
//    stats summary			# print summary information
//    dim 2				# dimension 2
//
//    data_size 5000			# 5000 data points
//    colors 30				# ...broken into 30 clusters
//    std_dev 0.025			# ...each with std deviation 0.025
//    distribution clus_gauss		# clustered gaussian distribution
//    seed 1				# random number seed
//  gen_data_pts			# generate the data points
//  
//    max_tot_stage 20 0 0 0		# terminate Lloyd's after 20 stages
//  print Running-lloyd's
//  run_kmeans lloyd			# run using Lloyd's algorithm
//  
//    max_swaps 3			# at most 3 swaps
//    max_tot_stage 0 3 0 2		# at most 3*k^2 = 1200 stages
//    max_run_stage 50			# at most 50 stages per run
//    min_accum_rdl 0.02		# stop run if distortion drops 2%
//  print Running-swap
//  run_kmeans swap			# run using swap heuristic
//------------------------------------------------------------------------

//------------------------------------------------------------------------
//  Statistics output levels (see KMeans.h for corresponding enumeration)
//------------------------------------------------------------------------

static const string stat_table[N_STAT_LEVELS] = {
	"silent",			// SILENT
	"exec_time",			// EXEC_TIME
	"summary",			// SUMMARY
	"phase",			// PHASE
	"run",				// RUN
	"stage",			// STAGE
	"step",				// STEP
	"centers",			// CENTERS
	"tree"};			// TREE

//------------------------------------------------------------------------
//  k-means algorithms
//	(See KMeans.h for coresponding enumeration)
//------------------------------------------------------------------------

static const string kmAlgTable[N_KM_ALGS] = {
	"lloyd",			// LLOYD only
	"swap",				// SWAP only
	"hybrid",			// HYBRID alternation
	"EZ-hybrid",			// EZ_HYBRID alternation
	"--illegal--"};			// RANDOM (not allowed)

//------------------------------------------------------------------------
//  Distributions
//------------------------------------------------------------------------

typedef enum {			// distributions
	UNIFORM,			// uniform over cube [-1,1]^d.
	GAUSS,				// Gaussian with mean 0
	LAPLACE,			// Laplacian, mean 0 and var 1
	CO_GAUSS,			// correlated Gaussian
	CO_LAPLACE,			// correlated Laplacian
	CLUS_GAUSS,			// clustered Gaussian
	CLUS_ORTH_FLATS,		// clustered on orthog flats
	CLUS_ELLIPSOIDS,		// clustered on ellipsoids
	MULTI_CLUS,			// multi-sized clusters
	N_DISTRIBS}
	Distrib;

static const string distr_table[N_DISTRIBS] = {
	"uniform",			// UNIFORM
	"gauss",			// GAUSS
	"laplace",			// LAPLACE
	"co_gauss",			// CO_GAUSS
	"co_laplace",			// CO_LAPLACE
	"clus_gauss",			// CLUS_GAUSS
	"clus_orth_flats",		// CLUS_ORTH_FLATS
	"clus_ellipsoids",		// CLUS_ELLIPSOIS
	"multi_clus"};			// MULTI_CLUS

//----------------------------------------------------------------------
//  Short utility functions
//	lookUp - look up a name in table and return index
//----------------------------------------------------------------------

static int lookUp(			// look up name in table
    const string &arg,			// name to look up
    const string *table,		// name table
    int		size)			// table size
{
    int i;
    for (i = 0; i < size; i++) {
	if (arg == table[i]) return i;
    }
    return i;
}

//----------------------------------------------------------------------
// elapsedTime
// Utility for computing elapsed time.
//----------------------------------------------------------------------

#ifndef CLOCKS_PER_SEC			// define clocks-per-second if needed
#define CLOCKS_PER_SEC          1000000	// (should be in time.h)
#endif

inline double elapsedTime(clock_t start) {
    return double(clock() - start)/double(CLOCKS_PER_SEC);
}

//------------------------------------------------------------------------
// Function declarations
//------------------------------------------------------------------------
static void runKmeans(			// run k-means algorithm
    KMalg		alg,		// which algorithm
    KMdataPtr		dataPts,	// data points
    KMterm		&term);		// termination condition

static void genDataPts(			// generate data points
    KMdataPtr		&dataPts,	// point array (returned)
    bool		new_clust);	// new cluster centers desired?

static void readDataPts(		// read data/query points from file
    KMdataPtr		&dataPts,	// point array (returned)
    int			n,		// desired number of points
    const string	&file_nm);	// file name

static void buildKcTree(		// build kc-tree for points
    KMdataPtr		dataPts);	// point array

//------------------------------------------------------------------------
//  Default execution parameters
//------------------------------------------------------------------------
const int	DEF_dim		= 2;		// dimension
const int	DEF_data_size	= 100;		// data size
const int	DEF_kcenters	= 5;		// number of centers

const int	DEF_max_swaps	= 1;		// max number of swaps
const double	DEF_damp_factor	= 1;		// Lloyd's dampening factor

const int	DEF_n_color	= 5;		// number of colors
const bool	DEF_new_clust	= false;	// new clusters flag
const int	DEF_max_dim	= 1;		// max flat dimension
const Distrib	DEF_distr	= UNIFORM;	// distribution
const double	DEF_std_dev	= 1.00;		// standard deviation
const double	DEF_corr_coef	= 0.05;		// correlation coef
const double	DEF_clus_sep	= 0.0;		// cluster separation

const int	DEF_max_visit	= 0;		// number of points visited

const int	DEF_seed	= 0;		// seed for random numbers

						// termination parameters
const KMterm	DEF_term(0, 0, 10, 1,		// max total stages (10*n)
			 0.10,			// min consec RDL
			 0.10,			// min accum RDL
			 100,			// max run stages
			 0.50,			// init. prob. of acceptance
			 20,			// temp. run length
			 0.75);			// temp. reduction factor

const StatLev	DEF_stats	= SUMMARY;	// statistics output level
const bool	DEF_print_points= false;	// print points?
const bool	DEF_show_assign	= false;	// show point assignments?
const bool	DEF_validate	= false;	// validate point assignments?
ostream* const	DEF_out		= &cout;	// standard output stream
ostream* const	DEF_err		= &cerr;	// error output stream
istream* const	DEF_in		= &cin;		// standard input stream

//------------------------------------------------------------------------
//  kmltest global variables - Execution options
//------------------------------------------------------------------------
					// basic size quantities
int		dim; 			// dimension
int		data_size; 		// data size
int		kcenters; 		// number of centers
int		max_swaps;		// max number of swaps per run
double		damp_factor;		// Lloyd's dampening factor

					// distribution parameters
int		n_color;		// number of colors (clusters)
bool		new_clust;		// generate new clusters?
int		max_dim;		// maximum flat dimension
Distrib		distr; 			// distribution
double		corr_coef; 		// correlation coef
double		std_dev; 		// standard deviation
double		std_dev_lo; 		// low standard deviation
double		std_dev_hi; 		// high standard deviation
double		clus_sep;		// cluster separation

					// other parameters
KMterm		term;			// termination parameters
bool		print_points;		// print points after generating?
bool		show_assign;		// show point assignments?
bool		validate;		// validate point assignments?

double		kc_build_time = 0.0;	// time to build the kc-tree
double		exec_time = 0.0;	// execution time

ifstream	inStream;		// input stream
ofstream	outStream;		// output stream

//------------------------------------------------------------------------
//  Initialize global parameters
//------------------------------------------------------------------------

static void initGlobals()
{
    dim			= DEF_dim;		// init execution parameters
    data_size		= DEF_data_size;
    kcenters		= DEF_kcenters;
    max_swaps		= DEF_max_swaps;
    damp_factor		= DEF_damp_factor;

    n_color		= DEF_n_color;		// distribution parameters
    new_clust		= DEF_new_clust;
    max_dim		= DEF_max_dim;
    distr		= DEF_distr;
    corr_coef		= DEF_corr_coef;
    std_dev		= DEF_std_dev;
    std_dev_lo		= DEF_std_dev;
    std_dev_hi		= DEF_std_dev;
    clus_sep		= DEF_clus_sep;
						// other parameters
    kmIdum		= -DEF_seed;		// init. global seed for ran0()

    term		= DEF_term;

    kmStatLev		= DEF_stats;		// level of statistics detail
    print_points	= DEF_print_points;	// print points?
    show_assign		= DEF_show_assign;	// show point assignments?
    validate		= DEF_validate;		// validate point assignments?
    kmOut		= DEF_out;
    kmErr		= DEF_err;
    kmIn		= DEF_in;

    kc_build_time	= 0.0;			// execution times
    exec_time		= 0.0;
}

//------------------------------------------------------------------------
// getCmdArgs - get and process command line arguments
//
//	Syntax:
//	kmltest [-i infile] [-o outfile]
//	
//	where:
//	    infile		directive input file
//	    outfile		output file
//
//	If file is not specified, then the standard input and standard
//	output are the defaults.
//------------------------------------------------------------------------

void getCmdArgs(int argc, char *argv[])
{
    int i = 1;
    while (i < argc) {				// read arguments
	if (!strcmp(argv[i], "-i")) {		// -i option
	    inStream.open(argv[++i], ios::in);	// open input file
	    if (!inStream) {
		kmError("Cannot open input file", KMabort);
	    }
	    kmIn = &inStream;			// make this input stream
	}
	else if (!strcmp(argv[i], "-o")) {	// -o option
	    outStream.open(argv[++i], ios::out);// open output file
	    if (!outStream) {
		kmError("Cannot open output file", KMabort);
	    }
	    kmOut = &outStream;			// make this output stream
	}
	else {					// illegal syntax
	    *kmErr << "Syntax:\n"
		   << "kmltest [-i infile] [-o outfile]\n"
		   << "    where:\n"
		   << "    infile         directive input file\n"
		   << "    outfile        output file\n";
	    exit(1);				// exit
	}
	i++;
    }
}

//------------------------------------------------------------------------
// getDirective - skip comments and read next directive
//	Returns true if directive read, and false if eof seen.
//------------------------------------------------------------------------

static bool skipComment(			// skip any comments
    istream		&in)			// input stream
{
    char ch = 0;
						// skip whitespace
    do { in.get(ch); } while (isspace(ch) && !in.eof());
    while (ch == '#' && !in.eof()) {		// comment?
						// skip to end of line
	do { in.get(ch); } while(ch != '\n' && !in.eof());
						// skip whitespace
	do { in.get(ch); } while(isspace(ch) && !in.eof());
    }
    if (in.eof()) return false;			// end of file
    in.putback(ch);				// put character back
    return true;
}

static bool getDirective(
    istream		&in,			// input stream
    string		&directive)		// directive storage
{
    if (!skipComment(in))			// skip comments
	return false;				// found eof along the way?
    in >> directive;				// read directive
    return true;
}

//------------------------------------------------------------------------
// main program - driver
//	The main program reads input options, invokes the necessary
//	routines to process them.
//------------------------------------------------------------------------

int main(int argc, char **argv)
{
    string	directive;			// input directive
    string	strArg;				// string argument
    double	dblArg;				// double argument
    int		intArg;				// integer argument

    KMdata*	dataPts = NULL;			// the data points
    KMalg	alg;				// which algorithm to use

    initGlobals();				// initialize global values
    getCmdArgs(argc, argv);

    kmOut->precision(4);			// output precision
    *kmOut << "------------------------------------------------------------\n"
	 << "kmltest: " << KMlongName << "\n"
	 << "    Version: " << KMversion << " " << KMversionCmt << "\n"
	 << "    Copyright: " << KMcopyright << ".\n"
	 << "    Latest Revision: " << KMlatestRev << ".\n"
	 << "------------------------------------------------------------\n\n";

    //--------------------------------------------------------------------
    //  Main input loop
    //--------------------------------------------------------------------
						// read input directive
    while (getDirective(*kmIn, directive)) {
	//----------------------------------------------------------------
	//  Read options
	//----------------------------------------------------------------
	if (directive == "quit") {
	    kmExit();
	}
	else if (directive == "dim") {
	    *kmIn >> dim;
	    new_clust = true;			// force new clusters
	}
	else if (directive == "data_size") {
	    *kmIn >> data_size;
	}
	else if (directive =="kcenters") {
	    *kmIn >> kcenters;
	}
	else if (directive =="max_swaps") {
	    *kmIn >> max_swaps;
	}
	else if (directive =="damp_factor") {
	    *kmIn >> damp_factor;
	}
	else if (directive =="colors") {
	    *kmIn >> n_color;
	    new_clust = true;			// force new clusters
	}
	else if (directive =="new_clust") {
	    new_clust = true;
	}
	else if (directive =="max_clus_dim") {
	    *kmIn >> max_dim;
	}
	else if (directive =="std_dev") {
	    *kmIn >> std_dev;
	}
	else if (directive =="std_dev_lo") {
	    *kmIn >> std_dev_lo;
	}
	else if (directive =="std_dev_hi") {
	    *kmIn >> std_dev_hi;
	}
	else if (directive =="corr_coef") {
	    *kmIn >> corr_coef;
	}
	//----------------------------------------------------------------
	//  termination conditions
	//----------------------------------------------------------------
	else if (directive == "max_tot_stage") {
	    for (int i = 0; i < KM_TERM_VEC_LEN; i++) {
		*kmIn >> dblArg;
		term.setMaxTotStage(i, dblArg);
	    }
	}
	else if (directive =="min_consec_rdl") {
	    *kmIn >> dblArg;
	    term.setMinConsecRDL(dblArg);
	}
	else if (directive =="min_accum_rdl") {
	    *kmIn >> dblArg;
	    term.setMinAccumRDL(dblArg);
	}
	else if (directive =="max_run_stage") {
	    *kmIn >> intArg;
	    term.setMaxRunStage(intArg);
	}
	else if (directive =="init_prob_accept") {
	    *kmIn >> dblArg;
	    term.setInitProbAccept(dblArg);
	}
	else if (directive =="temp_run_length") {
	    *kmIn >> intArg;
	    term.setTempRunLength(intArg);
	}
	else if (directive =="temp_reduc_fact") {
	    *kmIn >> dblArg;
	    term.setTempReducFact(dblArg);
	}
	//----------------------------------------------------------------
	//  seed option
	//	The seed is reset by setting the global kmIdum to the
	//	negation of the seed value.  See rand.cc.
	//----------------------------------------------------------------
	else if (directive =="seed") {
	    *kmIn >> kmIdum;
	    kmIdum = -kmIdum;
	}
	//----------------------------------------------------------------
	//  print points option
	//----------------------------------------------------------------
	else if (directive =="print_points") {
	    *kmIn >> strArg;			// input argument
	    if (strArg == "yes") {
		print_points = true;
	    }
	    else if (strArg == "no") {
		print_points = false;
	    }
	    else {
		*kmErr << "Argument: " << strArg << "\n";
		kmError("print_points arg must be \"yes\" or \"no\"", KMabort);
	    }
	}
	//----------------------------------------------------------------
	//  show assignments option
	//----------------------------------------------------------------
	else if (directive =="show_assignments") {
	    *kmIn >> strArg;			// input argument
	    if (strArg == "yes") {
		show_assign = true;
	    }
	    else if (strArg == "no") {
		show_assign = false;
	    }
	    else {
		*kmErr << "Argument: " << strArg << "\n";
		kmError("show_assignments arg must be \"yes\" or \"no\"", KMabort);
	    }
	}
	//----------------------------------------------------------------
	//  validate assignments option
	//----------------------------------------------------------------
	else if (directive =="validate") {
	    *kmIn >> strArg;			// input argument
	    if (strArg == "yes") {
		validate = true;
	    }
	    else if (strArg == "no") {
		validate = false;
	    }
	    else {
		*kmErr << "Argument: " << strArg << "\n";
		kmError("validate arg must be \"yes\" or \"no\"", KMabort);
	    }
	}
	//----------------------------------------------------------------
	//  distribution option
	//----------------------------------------------------------------
	else if (directive =="distribution") {
	    *kmIn >> strArg;			// input name and translate
	    distr = (Distrib) lookUp(strArg, distr_table, N_DISTRIBS);
	    if (distr >= N_DISTRIBS) {		// not something we recognize
		*kmErr << "Distribution: " << strArg << "\n";
		kmError("Unknown distribution", KMabort);
	    }
	}
	//----------------------------------------------------------------
	//  stats option
	//----------------------------------------------------------------
	else if (directive =="stats") {
	    *kmIn >> strArg;			// input name and translate
	    kmStatLev = (StatLev) lookUp(strArg, stat_table, N_STAT_LEVELS);
	    if (kmStatLev >= N_STAT_LEVELS) {	// not something we recognize
		*kmErr << "Stats level: " << strArg << "\n";
		kmError("Unknown statistics level", KMabort);
	    }
	    if (kmStatLev > SILENT)
		*kmOut << "stats = " << strArg << "\n";
	}
	//----------------------------------------------------------------
	//  print operation
	//----------------------------------------------------------------
	else if (directive =="print") {
	    *kmIn >> strArg;
	    *kmErr << "<" << strArg << ">" << endl;
	}
	//----------------------------------------------------------------
	//  title operation
	//----------------------------------------------------------------
	else if (directive =="title") {
	    *kmIn >> strArg;
	    if (kmStatLev > SILENT) {
		*kmOut << "title = " << strArg << endl;
	    }
	}
	//----------------------------------------------------------------
	//  gen_data_pts operation
	//----------------------------------------------------------------
	else if (directive =="gen_data_pts") {
	    genDataPts(				// create data points
		dataPts,			// data points (modified)
		new_clust);			// new clusters flag
	    new_clust = false;			// reset flag
	    buildKcTree(dataPts);		// build the kc-tree
	}
	//----------------------------------------------------------------
	//  read_data_pts operation
	//----------------------------------------------------------------
	else if (directive =="read_data_pts") {
	    *kmIn >> strArg;			// input file name
	    readDataPts(
		dataPts,			// data points (modified)
		data_size,			// array size
		strArg);			// file name
	    buildKcTree(dataPts);		// build the kc-tree
	}
	//----------------------------------------------------------------
	//  run_kmeans operation
	//----------------------------------------------------------------
	else if (directive =="run_kmeans") {
	    *kmIn >> strArg;			// input algorithm name
	    alg = (KMalg) lookUp(strArg, kmAlgTable, N_KM_ALGS);
	    if (alg >= N_KM_ALGS) {		// not something we recognize
		*kmErr << "Algorithm: " << strArg << "\n";
		kmError("Unknown k-means algorithm", KMabort);
	    }
	    if (dataPts == NULL) {		// data points must exist
		kmError("No data set has been generated", KMabort);
	    }
	    runKmeans(alg, dataPts, term);	// do it
	}
	//----------------------------------------------------------------
	//  Unknown directive
	//----------------------------------------------------------------
	else {
	    *kmErr << "Directive: " << directive << "\n";
	    // kmError("Unknown directive", KMabort);
	    kmError("Unknown directive", KMwarn);
	}
    }
    //--------------------------------------------------------------------
    //  End of input loop (close up)
    //--------------------------------------------------------------------
    if (kmStatLev > SILENT) {
	*kmOut << "<END_OF_RUN>\n";		// end of output marker
    }
    if (dataPts != NULL)  {			// deallocate data points
	delete dataPts;
    }
    kmExit();                                   // terminate
}

//------------------------------------------------------------------------
//  Print header for start of an execution
//------------------------------------------------------------------------

static void printHeader(
    KMalg		alg,			// the algorithm
    KMdataPtr		dataPts,		// data points
    const KMterm	&term)			// termination condition
{
    if (kmStatLev > SILENT) {
	*kmOut << "\n[Run_k-means:\n"
	     << "  k-means_alg      = " << kmAlgTable[alg] << "\n"
	     << "  data_size        = " << dataPts->getNPts() << "\n"
	     << "  kcenters         = " << kcenters << "\n"
	     << "  dim              = " << dim << "\n"
	     << "  max_tot_stage    = " << term.getMaxTotStage(kcenters,
	 						data_size) << "\n";
	switch (alg) {
	case LLOYD:
	    *kmOut  << "  max_run_stage    = "
		    << term.getMaxRunStage() << "\n"
		    << "  min_accum_rdl    = "
		    << term.getMinAccumRDL() << "\n";
	    break;
	case SWAP:
	    *kmOut  << "  max_swaps        = " << max_swaps << "\n";
	    break;
	case HYBRID:
	    *kmOut  << "  min_consec_rdl   = "
		    << term.getMinConsecRDL() << "\n"
		    << "  init_prob_accept = "
		    << term.getInitProbAccept() << "\n"
		    << "  temp_run_length  = "
		    << term.getTempRunLength() << "\n"
		    << "  temp_reduc_fact  = "
		    << term.getTempReducFact() << "\n";
	    break;
	case EZ_HYBRID:
	    *kmOut  << "  min_consec_rdl   = "
		    << term.getMinConsecRDL() << "\n";
	    break;
	default:
	    assert(false);			// shouldn't get here
	}
	*kmOut << "]" << endl;
    }
}

//------------------------------------------------------------------------
//  validateAssignments - validate center assignments
//  This procedure is given the assignments of data points to their
//  closest center, and determines (through simple brute-force search)
//  whether this assignment is correct.  This is used primarily for
//  debugging purposes.
//------------------------------------------------------------------------

void validateAssignments(
    KMdataPtr			data,		// the data points
    const KMfilterCenters&	ctrs,		// the center points
    KMctrIdxArray		closeCtr,	// closest centers
    double*			sqDist)		// squared distances
{
    int errCt = 0;				// number of errors
    KMdataArray dataPts = data->getPts();	// get points and centers
    KMcenterArray ctrPts = ctrs.getCtrPts();
    int nPts = data->getNPts();
    int kCtrs = ctrs.getK();

    *kmOut << "  (Validating assignments. ";

    for (int i = 0; i < nPts; i++) {
	KMdist minDist = KM_DIST_INF;		// distance to nearest center
	int minK = 0;				// index of this center
	KMpoint thisPt = dataPts[i];		// current data point

	for (int j = 0; j < kCtrs; j++) {	// compute closest candidate
	    KMdist dist = kmDist(dim, ctrPts[j], thisPt);
	    if (dist < minDist) {		// best so far?
		minDist = dist;			// yes, save it
		minK = j;			// ...and its index
	    }
	}
	if (sqDist[i] > minDist + KM_ERR ||	// distance mismatch
	    sqDist[i] < minDist - KM_ERR) {
	    *kmOut << "\n    Mismatch: data[" << i << "] assigned to ctr["
	    	<< closeCtr[i] << "] (" << sqDist[i]
		<< ") rather than ctr[" << minK << "] ("
		<< minDist << ")";
	    errCt++;
	}
    }
    *kmOut << " Found " << errCt << " mismatches.)" << endl;
}

//------------------------------------------------------------------------
//  Print summary at end of run
//------------------------------------------------------------------------

static void printSummary(
    KMlocalPtr		    theAlg,		// the algorithm
    KMdataPtr		    dataPts,		// data points
    KMfilterCenters&  	    ctrs)		// the centers
{
    int nStages = theAlg->getTotalStages();
    double totalTime = exec_time + kc_build_time;
    if (kmStatLev > SILENT) {
	*kmOut << "\n[k-means completed:\n"
	     << "  n_stages      = " << nStages << "\n";
	if (kmStatLev >= EXEC_TIME) {	// print exec time summary
	    *kmOut << "  total_time    = "
		 << totalTime << " sec\n"
		 << "  init_time     = "
		 << kc_build_time << " sec\n"
		 << "  stage_time    = "
		 << double(exec_time)/double(nStages)
		 << " sec/stage_(excl_init) "
		 << double(totalTime)/double(nStages)
		 << " sec/stage_(incl_init)\n"
		 << "  average_distort = "
		 << ctrs.getDist(false)/double(ctrs.getNPts())
		 << "\n";
	}
	if (kmStatLev >= SUMMARY) {	// print final results
	    int max_ctrs = kcenters;	// number of centers to print
	    if (kmStatLev < STAGE && max_ctrs > 10)
	      max_ctrs = 10;		// low interest? just print 10

	    *kmOut << "  (Final Center Points:\n";
	    ctrs.print();
	    *kmOut << "  )\n";
	}
	*kmOut << "]" << endl;
    }

    if (show_assign) {		// want to see point assignments?
	KMctrIdxArray closeCtr = new KMctrIdx[dataPts->getNPts()];
	double* sqDist = new double[dataPts->getNPts()];
	ctrs.getAssignments(closeCtr, sqDist);

	*kmOut	<< "  (Cluster assignments:\n"
		<< "    Point  Center  Squared Dist\n"
		<< "    -----  ------  ------------\n";
	for (int i = 0; i < dataPts->getNPts(); i++) {
	    *kmOut	<< "   " << setw(5) << i
			<< "   " << setw(5) << closeCtr[i]
			<< "   " << setw(10) << sqDist[i]
			<< "\n";
	}
	*kmOut << "  )\n";
	if (validate) {
	    validateAssignments(dataPts, ctrs, closeCtr, sqDist);
	}
	delete [] closeCtr;
	delete [] sqDist;
    }
}

//------------------------------------------------------------------------
//  runKmeans - run the k-means algorithm
//  This procedure is given an algorithm type, a pointer to a set of data
//  points and termination object.
//
//  This runs the k-means algorithm.  We assume that the data point set
//  has been generated (dataPts != NULL).  From these we create the
//  center points (using KMfilterCenters), print a header (if
//  desired), resets the performance statistics and resets the clock.
//
//  Based on the algorithm type we create an algorithm object of the
//  appropriate type and execute it.  Afterwards we print a summary of
//  the results.
//------------------------------------------------------------------------

static void runKmeans(KMalg alg, KMdataPtr dataPts, KMterm &term)
{
    if (dataPts == NULL) {			// failed to create data
      kmError("Data points have not been generated", KMabort);
    }
    						// center points
    KMfilterCenters ctrs(kcenters, *dataPts, damp_factor);
    printHeader(alg, dataPts, term);		// print header

    KMlocalPtr theAlg = NULL;			// the search algorithm
    switch (alg) {				// select the search algorithm
    case LLOYD:					// Lloyd's algorithm
	theAlg = new KMlocalLloyds(ctrs, term);
	break;
    case SWAP:					// the swap heuristic
	theAlg = new KMlocalSwap(ctrs, term, max_swaps);
	break;
    case HYBRID:				// the hybrid algorithm
	theAlg = new KMlocalHybrid(ctrs, term);
	break;
    case EZ_HYBRID:				// the EZ-hybrid algorithm
	theAlg = new KMlocalEZ_Hybrid(ctrs, term);
	break;
    default:
	kmError("Internal error: Invalid algorithm", KMabort);
	break;
    }

    clock_t start = clock();			// start the clock
    ctrs = theAlg->execute();			// execute the algorithm
    exec_time = elapsedTime(start);		// get elapsed time
    						// print summary
    printSummary(theAlg, dataPts, ctrs);
}

//------------------------------------------------------------------------
//  Build kc-tree for the points
//	This should be called whenever the point set is modified
//	This time to construct the tree is saved in the global variable,
//	kc_build_time.
//------------------------------------------------------------------------

static void buildKcTree(		// build kc-tree for points
    KMdataPtr		dataPts)	// point array
{
    clock_t start = clock();			// start the clock
    dataPts->buildKcTree();			// build the tree
    kc_build_time = elapsedTime(start);		// get elapsed time

    if (kmStatLev >= TREE) {			// print the tree (if req'd)
	*kmOut << "Contents of the kc-tree: [\n";
	dataPts->getKcTree()->print(false);
	*kmOut << "]" << endl;
    }
}

//------------------------------------------------------------------------
// Print summary of distribution.
//------------------------------------------------------------------------

void printDistribSummary(
    KMpointArray	pa,		// point array
    int			nClus)		// number of clusters (for MULTI_CLUS)
{
    if (kmStatLev > SILENT) {
	*kmOut << "[Generating Data Points:\n"
	     << "  data_size     = " << data_size << "\n"
	     << "  dim           = " << dim << "\n";
						// output distribution info
	*kmOut << "  distribution  = " << distr_table[distr] << "\n";
	if (kmIdum < 0)
	    *kmOut << "  seed          = " << kmIdum << "\n";
	if (distr == GAUSS
	 || distr == CLUS_GAUSS
	 || distr == MULTI_CLUS
	 || distr == CLUS_ORTH_FLATS)
	    *kmOut << "  std_dev       = " << std_dev << "\n";
	if (distr == CLUS_ELLIPSOIDS) {
	    *kmOut << "  std_dev       = " << std_dev << " (small) \n"
		   << "  std_dev_lo    = " << std_dev_lo << "\n"
		   << "  std_dev_hi    = " << std_dev_hi << "\n";
	}
	if (distr == CO_GAUSS        || distr == CO_LAPLACE)
	    *kmOut << "  corr_coef     = " << corr_coef << "\n";
	if (distr == CLUS_GAUSS      || distr == CLUS_ORTH_FLATS
	 || distr == CLUS_ELLIPSOIDS) {
	    *kmOut << "  colors        = " << n_color << "\n";
	    if (new_clust)
		*kmOut << "  (cluster centers regenerated)\n";
	}
	if (distr == CLUS_ORTH_FLATS || distr == CLUS_ELLIPSOIDS) {
	    *kmOut << "  max_dim       = " << max_dim << "\n";
	}
	if (distr == CLUS_GAUSS) {
	    *kmOut << "  cluster_sep   = " << clus_sep << "\n";
	}
	if (distr == MULTI_CLUS) {
	    *kmOut << "  n_clusters    = " << nClus << "\n";
	}
    }
    if (kmStatLev >= TREE) {			// want to see points?
						// clustered gaussian data?
	if (distr == CLUS_GAUSS) {
	    KMpointArray clusts = kmGetCGclusters();
	    kmPrintPts("Cluster_Centers", clusts, n_color, dim);
	}
    }
    if (print_points) {				// print the points?
	kmPrintPts("Data_Points", pa, data_size, dim);
    }
    *kmOut << "]" << endl;
}
//------------------------------------------------------------------------
//  Generate data points from a distribution
//	genDataPts calls the appropriate generation function and
//	prints the summary.
//------------------------------------------------------------------------

static void genDataPts(
    KMdataPtr		&dataPts,	// pointer to data points (returned)
    bool		new_clust)	// new cluster centers desired?
{
    int nClus;					// number of clusters (ignored)

    if (dataPts == NULL) {			// allocate storage for points
	dataPts = new KMdata(dim, data_size);	// allocate new structure
    }
    else {
	dataPts->resize(dim, data_size);		// else resize
    }
    KMpointArray pa = dataPts->getPts();	// get the point array

    switch (distr) {
	case UNIFORM:				// uniform over cube [-1,1]^d.
	    kmUniformPts(pa, data_size, dim);
	    break;
	case GAUSS:				// Gaussian with mean 0
	    kmGaussPts(pa, data_size, dim, std_dev);
	    break;
	case LAPLACE:				// Laplacian, mean 0 and var 1
	    kmLaplacePts(pa, data_size, dim);
	    break;
	case CO_GAUSS:				// correlated Gaussian
	    kmCoGaussPts(pa, data_size, dim, corr_coef);
	    break;
	case CO_LAPLACE:			// correlated Laplacian
	    kmCoLaplacePts(pa, data_size, dim, corr_coef);
	    break;
	case CLUS_GAUSS:			// clustered Gaussian
	    kmClusGaussPts(pa, data_size, dim, n_color, new_clust,
	    		std_dev, &clus_sep);
	    break;
	case CLUS_ORTH_FLATS:			// clustered on orthog flats
	    kmClusOrthFlats(pa, data_size, dim, n_color, new_clust,
	    		std_dev, max_dim);
	    break;
	case CLUS_ELLIPSOIDS:			// clustered ellipsoids
	    kmClusEllipsoids(pa, data_size, dim, n_color, new_clust,
	    		std_dev, std_dev_lo, std_dev_hi, max_dim);
	    break;
	case MULTI_CLUS:			// multi-sized clusters
	    kmMultiClus(pa, data_size, dim, nClus, std_dev);
	    break;
	default:
	    kmError("INTERNAL ERROR: Unknown distribution", KMabort);
	    break;
    }
    printDistribSummary(pa, nClus);		// print summary of distrib
}

//------------------------------------------------------------------------
// readDataPts - read a set of data points from a file
//------------------------------------------------------------------------

static void readDataPts(
    KMdataPtr		&dataPts,	// point array (returned)
    int			array_size,	// array size
    const string	&file_nm)	// file name
{
    int i;
    //--------------------------------------------------------------------
    //  Open input file and read points
    //--------------------------------------------------------------------
    ifstream in_file(file_nm.c_str());		// try to open data file
    if (!in_file) {
	*kmErr << "File name: " << file_nm << "\n";
	kmError("Cannot open input data/query file", KMabort);
    }

    if (dataPts == NULL) {			// allocate storage for points
	dataPts = new KMdata(dim, array_size);	// allocate new structure
    }
    else {
	dataPts->resize(dim, array_size);		// else resize
    }

    for (i = 0; i < array_size; i++) {		// read the data
	if (!(in_file >> (*dataPts)[i][0])) break;
	for (int d = 1; d < dim; d++) {
	    in_file >> (*dataPts)[i][d];
	}
    }

    char ignore_me;				// character for EOF test
    in_file >> ignore_me;			// try to get one more character
    if (!in_file.eof()) {			// exhausted space before eof
	kmError("data_size too small; input file truncated", KMwarn);
    }
    int n = i;
    dataPts->setNPts(n);			// set number of points

    //--------------------------------------------------------------------
    //  Print summary
    //--------------------------------------------------------------------
    if (kmStatLev > SILENT) {
	*kmOut << "[Read Data Points:\n"
	     << "  data_size  = " << n << "\n"
	     << "  file_name  = " << file_nm << "\n"
	     << "  dim        = " << dim << "\n";
	if (print_points) {			// print the points?
	    kmPrintPts("Data_Points", dataPts->getPts(), n, dim);
	}
	*kmOut << "]" << endl;
    }
}
