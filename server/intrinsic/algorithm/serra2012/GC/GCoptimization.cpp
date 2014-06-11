#include "energy.h"
#include "graph.h"
#include "GCoptimization.h"
#include <stdio.h>
#include <time.h>
#include <stdlib.h>
#define MAX_INTT 1000000000


/**************************************************************************************/

void GCoptimization::initialize_memory()
{
    int i = 0;
    
	m_lookupPixVar = (PixelType *) new PixelType[m_num_pixels];
	m_labelTable   = (LabelType *) new LabelType[m_num_labels];

	terminateOnError( !m_lookupPixVar || !m_labelTable,"Not enough memory");

	for ( i = 0; i < m_num_labels; i++ )
		m_labelTable[i] = i;

	for ( i = 0; i < m_num_pixels; i++ )
		m_lookupPixVar[i] = -1;

}


/**************************************************************************************/

void GCoptimization::commonGridInitialization(PixelType width, PixelType height, int nLabels)
{
	terminateOnError( (width < 0) || (height <0) || (nLabels <0 ),"Illegal negative parameters");

	m_width              = width;
	m_height             = height;
	m_num_pixels         = width*height;
	m_num_labels         = nLabels;
	m_grid_graph         = 1;
		
	
	srand(time(NULL));
}
/**************************************************************************************/

void GCoptimization::commonNonGridInitialization(PixelType nupixels, int num_labels)
{
	terminateOnError( (nupixels <0) || (num_labels <0 ),"Illegal negative parameters");

	m_num_labels		 = num_labels;
	m_num_pixels		 = nupixels;
	m_grid_graph         = 0;

	m_neighbors = (LinkedBlockList *) new LinkedBlockList[nupixels];

	terminateOnError(!m_neighbors,"Not enough memory");

}

/**************************************************************************************/

void GCoptimization::commonInitialization(int dataSetup, int smoothSetup)
{
	int i;

	m_random_label_order = 1;
	m_dataInput          = dataSetup;
	m_smoothInput        = smoothSetup;


	if (m_dataInput == SET_INDIVIDUALLY )
	{
		m_datacost    = (EnergyTermType *) new EnergyTermType[m_num_labels*m_num_pixels];
		terminateOnError(!m_datacost,"Not enough memory");
		for ( i = 0; i < m_num_labels*m_num_pixels; i++ ) 
			m_datacost[i] = (EnergyTermType) 0;
		m_dataType = ARRAY;
	}
	else m_dataType = NONE;


	if ( m_smoothInput == SET_INDIVIDUALLY )
	{
		m_smoothcost  = (EnergyTermType *) new EnergyTermType[m_num_labels*m_num_labels];
		terminateOnError(!m_smoothcost,"Not enough memory");
		for ( i = 0; i < m_num_labels*m_num_labels; i++ ) 
			m_smoothcost[i] = (EnergyTermType) 0;

		m_smoothType      = ARRAY;
		m_varying_weights = 0;
	}
	else m_smoothType  = NONE;


	initialize_memory();
	srand(time(NULL));
    // <!-- bagon
    // sign class as valid
    class_sig = VALID_CLASS_SIGNITURE;
    // bagon -->
}

/**************************************************************************************/
/* Use this constructor only for grid graphs                                          */
GCoptimization::GCoptimization(PixelType width,PixelType height,int nLabels,int dataSetup, int smoothSetup )
{
	commonGridInitialization(width,height,nLabels);
	
	m_labeling           = (LabelType *) new LabelType[m_num_pixels];
	terminateOnError(!m_labeling,"out of memory");
	for ( int i = 0; i < m_num_pixels; i++ ) m_labeling[i] = (LabelType) 0;

	m_deleteLabeling = 1;
	commonInitialization(dataSetup,smoothSetup);	
}

/**************************************************************************************/
/* Use this constructor only for grid graphs                                          */
GCoptimization::GCoptimization(LabelType *m_answer,PixelType width,PixelType height,int nLabels,
							   int dataSetup, int smoothSetup) 
						   
{
	commonGridInitialization(width,height,nLabels);

	m_labeling = m_answer;

	
	for ( int i = 0; i < m_num_pixels; i++ )
		terminateOnError(m_labeling[i] < 0 || m_labeling[i] >= nLabels,"Initial labels are out of valid range");
	
	m_deleteLabeling = 0;
		
	commonInitialization(dataSetup,smoothSetup);	
}

/**************************************************************************************/
/* Use this constructor for general graphs                                            */
GCoptimization::GCoptimization(PixelType nupixels,int nLabels,int dataSetup, int smoothSetup )
{

	commonNonGridInitialization(nupixels, nLabels);
	
	m_labeling           = (LabelType *) new LabelType[m_num_pixels];
	terminateOnError(!m_labeling,"out of memory");
	for ( int i = 0; i < nupixels; i++ ) m_labeling[i] = (LabelType) 0;

	m_deleteLabeling = 1;

	commonInitialization(dataSetup,smoothSetup);	
}

/**************************************************************************************/
/* Use this constructor for general graphs                                            */
GCoptimization::GCoptimization(LabelType *m_answer, PixelType nupixels,int nLabels,int dataSetup, int smoothSetup)
{
	commonNonGridInitialization(nupixels, nLabels);
	

	m_labeling = m_answer;
	for ( int i = 0; i < m_num_pixels; i++ )
		terminateOnError(m_labeling[i] < 0 || m_labeling[i] >= nLabels,"Initial labels are out of valid range");

	m_deleteLabeling = 0;

	commonInitialization(dataSetup,smoothSetup);	
}

/**************************************************************************************/

void GCoptimization::setData(EnergyTermType* dataArray)
{
	terminateOnError(m_dataType != NONE,
		            "ERROR: you already set the data, or said you'll use member function setDataCost() to set data");	

    // <!-- bagon
    /* allocate memory dinamiocally */
    m_datacost = (EnergyTermType *) new EnergyTermType[m_num_pixels*m_num_labels];
    for ( int i(0); i < m_num_pixels*m_num_labels; i++ )
        m_datacost[i] = dataArray[i];
	// m_datacost  = dataArray;
    // bagon -->
	m_dataType  = ARRAY;
}

/**************************************************************************************/

void GCoptimization::setData(dataFnPix dataFn)
{
	terminateOnError(m_dataType != NONE,
		            "ERROR: you already set the data, or said you'll use member function setDataCost() to set data");	
	
	m_dataFnPix = dataFn;
	m_dataType  = FUNCTION_PIX;
}

/**************************************************************************************/

void GCoptimization::setData(dataFnCoord dataFn)
{
	terminateOnError(m_dataType != NONE,
		            "ERROR: you already set the data, or said you'll use member function setDataCost() to set data");	

	terminateOnError( !m_grid_graph,"Cannot use data function based on coordinates for non-grid graph");

	m_dataFnCoord = dataFn;
	m_dataType    = FUNCTION_COORD;
}

/**************************************************************************************/

void GCoptimization::setSmoothness(EnergyTermType* V)
{

	terminateOnError(m_smoothType != NONE,
		            "ERROR: you already set smoothness, or said you'll use member function setSmoothCost() to set Smoothness Costs");	


	m_smoothType = ARRAY;
    // <!-- bagon
    /* allocate memory dinamiocally */
    m_smoothcost = (EnergyTermType *) new EnergyTermType[m_num_labels*m_num_labels];
    for ( int i(0); i < m_num_labels*m_num_labels; i++ )
        m_smoothcost[i] = V[i];
	// m_smoothcost = V;
    // bagon -->
    m_varying_weights = 0;

}

/**************************************************************************************/
void GCoptimization::setSmoothness(EnergyTermType* V,EnergyTermType* hCue, EnergyTermType* vCue)
{
	terminateOnError(m_smoothType != NONE,
		            "ERROR: you already set smoothness, or said you'll use member function setSmoothCost() to set Smoothness Costs");	

	terminateOnError(!m_grid_graph,
		            "ERROR: for a grid graph, you can't use vertical and horizontal cues.  Use setNeighbors() member function to encode spatially varying cues");	

	m_varying_weights = 1;

    m_smoothType      = ARRAY;
    // <!-- bagon
    /* allocate memory dinamiocally */
    int i = 0;
    m_smoothcost = (EnergyTermType *) new EnergyTermType[m_num_labels*m_num_labels];
    for ( i = 0; i < m_num_labels*m_num_labels; i++ )
        m_smoothcost[i] = V[i];
    
    m_vertWeights = (EnergyTermType *) new EnergyTermType[m_num_pixels];
    for ( i = 0; i < m_num_pixels; i++ )
        m_vertWeights[i] = vCue[i];
    
    m_horizWeights = (EnergyTermType *) new EnergyTermType[m_num_pixels];
    for ( i = 0; i < m_num_pixels; i++ )
        m_horizWeights[i] = hCue[i];
    
	//m_vertWeights     = vCue;
	//m_horizWeights    = hCue;
	//m_smoothcost      = V;
    // bagon -->
}

/**************************************************************************************/

void GCoptimization::setSmoothness(smoothFnCoord horz_cost, smoothFnCoord vert_cost)
{

	terminateOnError(m_smoothType != NONE,
		            "ERROR: you already set smoothness, or said you'll use member function setSmoothCost() to set Smoothness Costs");	

	terminateOnError( !m_grid_graph,"Cannot use smoothness function based on coordinates for non-grid graph");

	m_smoothType    = FUNCTION_COORD;
	m_horz_cost     = horz_cost;
	m_vert_cost     = vert_cost;
}

/**************************************************************************************/

void GCoptimization::setSmoothness(smoothFnPix cost)
{
	terminateOnError(m_smoothType != NONE,
		            "ERROR: you already set smoothness, or said you'll use member function setSmoothCost() to set Smoothness Costs");	

	m_smoothType    = FUNCTION_PIX;
	m_smoothFnPix   = cost;
}

/**************************************************************************************/
// <!-- bagon
void 
GCoptimization::SetAllLabels(const LabelType* labels)
{
    for( int i(0); i < m_num_pixels; i++ ) {
        terminateOnError( (labels[i]<0) || (labels[i]>=m_num_labels), "Wrong label value");
        m_labeling[i] = labels[i];
    }
}
/**************************************************************************************/    
void 
GCoptimization::ExportLabels(LabelType* labels)
{
    for( int i(0); i < m_num_pixels; i++)
        labels[i] = m_labeling[i];
}
// bagon -->
/**************************************************************************************/    
GCoptimization::EnergyType GCoptimization::giveDataEnergy()
{
	if ( m_dataType == ARRAY) 
		return(giveDataEnergyArray());
	else if ( m_dataType == FUNCTION_PIX )
		return(giveDataEnergyFnPix());
	else if (m_dataType == FUNCTION_COORD ) return(giveDataEnergyFnCoord());
	else terminateOnError(1,"Did not initialize the data costs yet");

	return(0);
}

/**************************************************************************************/
	
GCoptimization::EnergyType GCoptimization::giveDataEnergyArray()
{
	EnergyType eng = (EnergyType) 0;


	for ( int i = 0; i < m_num_pixels; i++ ) if (m_labeling[i] != m_num_labels+1)
		eng = eng + m_datacost(i,m_labeling[i]);

	return(eng);
}

/**************************************************************************************/
	
GCoptimization::EnergyType GCoptimization::giveDataEnergyFnPix()
{

	EnergyType eng = (EnergyType) 0;

	for ( int i = 0; i < m_num_pixels; i++ )
		eng = eng + m_dataFnPix(i,m_labeling[i]);

	return(eng);
}
/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveDataEnergyFnCoord()
{
	EnergyType eng = (EnergyType) 0;

	for ( int y = 0; y < m_height; y++ )
		for ( int x = 0; x < m_width; x++ )
			eng = eng + m_dataFnCoord(x,y,m_labeling[x+y*m_width]);

	return(eng);

}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy()
{

	if ( m_grid_graph )
	{
		if ( m_smoothType == ARRAY )
		{
			if (m_varying_weights) return(giveSmoothEnergy_G_ARRAY_VW());
			else return(giveSmoothEnergy_G_ARRAY());
		}
		else if ( m_smoothType == FUNCTION_PIX ) return(giveSmoothEnergy_G_FnPix());
		else if ( m_smoothType == FUNCTION_COORD ) return(giveSmoothEnergy_G_FnCoord());
		else terminateOnError(1,"Did not initialize smoothness costs yet, can't compute smooth energy");
	}
	else
	{
		if ( m_smoothType == ARRAY ) return(giveSmoothEnergy_NG_ARRAY());
		else if ( m_smoothType == FUNCTION_PIX ) return(giveSmoothEnergy_NG_FnPix());
		else terminateOnError(1,"Did not initialize smoothness costs yet, can't compute smooth energy");
	}
	return(0);

}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_NG_FnPix()
{

	EnergyType eng = (EnergyType) 0;
	int i;
	Neighbor *temp; 

	for ( i = 0; i < m_num_pixels; i++ )
		if ( !m_neighbors[i].isEmpty() )
		{
			m_neighbors[i].setCursorFront();
			while ( m_neighbors[i].hasNext() )
			{
				temp = (Neighbor *) m_neighbors[i].next();
				if ( i < temp->to_node )
					eng = eng + m_smoothFnPix(i,temp->to_node, m_labeling[i],m_labeling[temp->to_node]);
			}
		}
		
	return(eng);
	
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_NG_ARRAY()
{
	EnergyType eng = (EnergyType) 0;
	int i;
	Neighbor *temp; 

	for ( i = 0; i < m_num_pixels; i++ )
		if ( !m_neighbors[i].isEmpty() )
		{
			m_neighbors[i].setCursorFront();
			while ( m_neighbors[i].hasNext() )
			{
				temp = (Neighbor *) m_neighbors[i].next();

				if ( i < temp->to_node )
					eng = eng + m_smoothcost(m_labeling[i],m_labeling[temp->to_node])*(temp->weight);

			}
		}

	return(eng);
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_G_ARRAY_VW()
{

	EnergyType eng = (EnergyType) 0;
	int x,y,pix;

	// printf("\nIn right place");
	
	for ( y = 0; y < m_height; y++ )
		for ( x = 1; x < m_width; x++ ) if ((m_labeling[x+y*m_width-1] != m_num_labels +1) &&(m_labeling[x+y*m_width] != m_num_labels +1) ) 
		{
			pix = x+y*m_width;
			eng = eng + m_smoothcost(m_labeling[pix],m_labeling[pix-1])*m_horizWeights[pix-1];
		}

	for ( y = 1; y < m_height; y++ )
		for ( x = 0; x < m_width; x++ )if ((m_labeling[x+y*m_width-m_width] != m_num_labels +1) &&(m_labeling[x+y*m_width] != m_num_labels +1) ) 
		{
			pix = x+y*m_width;
			eng = eng + m_smoothcost(m_labeling[pix],m_labeling[pix-m_width])*m_vertWeights[pix-m_width];
		}

	
	return(eng);
	
}
/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_G_ARRAY()
{

	EnergyType eng = (EnergyType) 0;
	int x,y,pix;


	for ( y = 0; y < m_height; y++ )
		for ( x = 1; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_smoothcost(m_labeling[pix],m_labeling[pix-1]);
		}

	for ( y = 1; y < m_height; y++ )
		for ( x = 0; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_smoothcost(m_labeling[pix],m_labeling[pix-m_width]);
		}

	return(eng);
	
}
/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_G_FnPix()
{

	EnergyType eng = (EnergyType) 0;
	int x,y,pix;


	for ( y = 0; y < m_height; y++ )
		for ( x = 1; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_smoothFnPix(pix,pix-1,m_labeling[pix],m_labeling[pix-1]);
		}

	for ( y = 1; y < m_height; y++ )
		for ( x = 0; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_smoothFnPix(pix,pix-m_width,m_labeling[pix],m_labeling[pix-m_width]);
		}

	return(eng);
	
}
/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::giveSmoothEnergy_G_FnCoord()
{

	EnergyType eng = (EnergyType) 0;
	int x,y,pix;


	for ( y = 0; y < m_height; y++ )
		for ( x = 1; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_horz_cost(x-1,y,m_labeling[pix],m_labeling[pix-1]);
		}

	for ( y = 1; y < m_height; y++ )
		for ( x = 0; x < m_width; x++ )
		{
			pix = x+y*m_width;
			eng = eng + m_vert_cost(x,y-1,m_labeling[pix],m_labeling[pix-m_width]);
		}

	return(eng);
	
}

/**************************************************************************************/
 
GCoptimization::EnergyType GCoptimization::compute_energy()
{
	return(giveDataEnergy()+giveSmoothEnergy());
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::expansion(int max_num_iterations)
{
	return(start_expansion(max_num_iterations)); 
}

/**************************************************************************************/


GCoptimization::EnergyType GCoptimization::expansion()
{
	return(start_expansion(MAX_INTT));
}

/**************************************************************************************/


GCoptimization::EnergyType GCoptimization::start_expansion(int max_num_iterations )
{
	
	int curr_cycle = 1;
	EnergyType new_energy,old_energy;
	

	new_energy = compute_energy();

	old_energy = (new_energy+1)*10; // BAGON changed init value to exceed current energy by factor of 10 (thanks to A. Khan)

	while ( old_energy > new_energy  && curr_cycle <= max_num_iterations)
	{
		old_energy = new_energy;
		new_energy = oneExpansionIteration();
		
		curr_cycle++;	
	}

	return(new_energy);
}

/****************************************************************************/

void GCoptimization::scramble_label_table()
{
   LabelType r1,r2,temp;
   int num_times,cnt;


   num_times = m_num_labels*2;

   for ( cnt = 0; cnt < num_times; cnt++ )
   {
      r1 = rand()%m_num_labels;  
      r2 = rand()%m_num_labels;  

      temp             = m_labelTable[r1];
      m_labelTable[r1] = m_labelTable[r2];
      m_labelTable[r2] = temp;
   }
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::alpha_expansion(LabelType label)
{
	terminateOnError( label < 0 || label >= m_num_labels,"Illegal Label to Expand On");

	perform_alpha_expansion(label);
	return(compute_energy());
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::alpha_expansion(LabelType alpha_label, PixelType *pixels, int num )
{
	PixelType i,size = 0; 
	Energy *e = new Energy(mexErrMsgTxt);
	


	for ( i = 0; i<num ; i++ )
	{
		if ( m_labeling[pixels[i]] != alpha_label )
		{
			m_lookupPixVar[pixels[i]] = i;
		}
	}

	
	if ( size > 0 ) 
	{
		Energy::Var *variables = (Energy::Var *) new Energy::Var[size];

		for ( i = 0; i < size; i++ )
			variables[i] = e ->add_variable();

		if ( m_dataType == ARRAY ) add_t_links_ARRAY(e,variables,size,alpha_label);
		else  if  ( m_dataType == FUNCTION_PIX ) add_t_links_FnPix(e,variables,size,alpha_label);
		else  add_t_links_FnCoord(e,variables,size,alpha_label);


		if ( m_grid_graph )
		{
			if ( m_smoothType == ARRAY )
			{
				if (m_varying_weights) set_up_expansion_energy_G_ARRAY_VW_pix(size,alpha_label,e,variables,pixels,num);
				else set_up_expansion_energy_G_ARRAY_pix(size,alpha_label,e,variables,pixels,num);
			}
			else if ( m_smoothType == FUNCTION_PIX ) {
                mexErrMsgIdAndTxt("GraphCut:internal", "NOT SUPPORTED YET,exiting!");
//				printf("NOT SUPPORTED YET,exiting!");
//				exit(0);
				//if ( m_smoothType == FUNCTION_PIX ) set_up_expansion_energy_G_FnPix_pix(size,alpha_label,e,variables);
			}
			else
			{
                mexErrMsgIdAndTxt("GraphCut:internal", "NOT SUPPORTED YET,exiting!");
//				printf("NOT SUPPORTED YET,exiting!");
//				exit(0);
				//set_up_expansion_energy_G_FnCoord_pix(size,alpha_label,e,variables);
			}
			
		}
		else
		{
            mexErrMsgIdAndTxt("GraphCut:internal", "NOT SUPPORTED YET,exiting!");
//			printf("NOT SUPPORTED YET,exiting!");
//			exit(0);
			/*if ( m_smoothType == ARRAY ) set_up_expansion_energy_NG_ARRAY_pix(size,alpha_label,e,variables);
			else if ( m_smoothType == FUNCTION_PIX ) set_up_expansion_energy_NG_FnPix_pix(size,alpha_label,e,variables);*/
		}
		
		e -> minimize();
	
	

		for ( i = 0; i < num; i++ )
		{
			if ( m_labeling[pixels[i]] != alpha_label )
			{
				if ( e->get_var(variables[i]) == 0 )
					m_labeling[pixels[i]] = alpha_label;
			}
			m_lookupPixVar[pixels[i]] = -1;
		}

		delete [] variables;
	}

	delete e;

	return(compute_energy());
}

/**************************************************************************************/

void GCoptimization::add_t_links_ARRAY(Energy *e,Energy::Var *variables,int size,LabelType alpha_label)
{
	for ( int i = 0; i < size; i++ )
		e -> add_term1(variables[i], m_datacost(m_lookupPixVar[i],alpha_label),
		                             m_datacost(m_lookupPixVar[i],m_labeling[m_lookupPixVar[i]]));

}

/**************************************************************************************/

void GCoptimization::add_t_links_FnPix(Energy *e,Energy::Var *variables,int size,LabelType alpha_label)
{
	for ( int i = 0; i < size; i++ )
		e -> add_term1(variables[i], m_dataFnPix(m_lookupPixVar[i],alpha_label),
		                             m_dataFnPix(m_lookupPixVar[i],m_labeling[m_lookupPixVar[i]]));

}
/**************************************************************************************/

void GCoptimization::add_t_links_FnCoord(Energy *e,Energy::Var *variables,int size,LabelType alpha_label)
{
	int x,y;

	for ( int i = 0; i < size; i++ )
	{

		y = m_lookupPixVar[i]/m_width;
		x = m_lookupPixVar[i] - y*m_width;

		e -> add_term1(variables[i], m_dataFnCoord(x,y,alpha_label),
		                             m_dataFnCoord(x,y,m_labeling[m_lookupPixVar[i]]));
	}

}

/**************************************************************************************/

void GCoptimization::perform_alpha_expansion(LabelType alpha_label)
{
	PixelType i,size = 0; 
	Energy *e = new Energy(mexErrMsgTxt);
	

	
	for ( i = 0; i < m_num_pixels; i++ )
	{
		if ( m_labeling[i] != alpha_label )
		{
			m_lookupPixVar[size] = i;
			size++;
		}
	}

		
	if ( size > 0 ) 
	{
		Energy::Var *variables = (Energy::Var *) new Energy::Var[size];

		for ( i = 0; i < size; i++ )
			variables[i] = e ->add_variable();

		if ( m_dataType == ARRAY ) add_t_links_ARRAY(e,variables,size,alpha_label);
		else  if  ( m_dataType == FUNCTION_PIX ) add_t_links_FnPix(e,variables,size,alpha_label);
		else  add_t_links_FnCoord(e,variables,size,alpha_label);


		if ( m_grid_graph )
		{
			if ( m_smoothType == ARRAY )
			{
				if (m_varying_weights) set_up_expansion_energy_G_ARRAY_VW(size,alpha_label,e,variables);
				else set_up_expansion_energy_G_ARRAY(size,alpha_label,e,variables);
			}
			else if ( m_smoothType == FUNCTION_PIX ) set_up_expansion_energy_G_FnPix(size,alpha_label,e,variables);
			else  set_up_expansion_energy_G_FnCoord(size,alpha_label,e,variables);
			
		}
		else
		{
			if ( m_smoothType == ARRAY ) set_up_expansion_energy_NG_ARRAY(size,alpha_label,e,variables);
			else if ( m_smoothType == FUNCTION_PIX ) set_up_expansion_energy_NG_FnPix(size,alpha_label,e,variables);
		}
		
		e -> minimize();
	
	

		for ( i = 0,size = 0; i < m_num_pixels; i++ )
		{
			if ( m_labeling[i] != alpha_label )
			{
				if ( e->get_var(variables[size]) == 0 )
					m_labeling[i] = alpha_label;

				size++;
			}
		}

		delete [] variables;
	}

	delete e;
}

/**********************************************************************************************/
/* Performs alpha-expansion for non regular grid graph for case when energy terms are NOT     */
/* specified by a function */

void GCoptimization::set_up_expansion_energy_NG_ARRAY(int size, LabelType alpha_label,Energy *e,Energy::Var *variables )
{
	EnergyTermType weight;
	Neighbor *tmp;
	int i,nPix,pix;;



	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		m_lookupPixVar[pix] = i;

		if ( !m_neighbors[pix].isEmpty() )
		{
			m_neighbors[pix].setCursorFront();
			
			while ( m_neighbors[pix].hasNext() )
			{
				tmp = (Neighbor *) (m_neighbors[pix].next());
				nPix   = tmp->to_node;
				weight = tmp->weight;
				
				if ( m_labeling[nPix] != alpha_label )
				{
					if ( pix < nPix )
						e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
							          m_smoothcost(alpha_label,alpha_label)*weight,
									  m_smoothcost(alpha_label,m_labeling[nPix])*weight,
									  m_smoothcost(m_labeling[pix],alpha_label)*weight,
									  m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight);
				}
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,alpha_label)*weight,
  					                       m_smoothcost(m_labeling[pix],alpha_label)*weight);
				
			}
		}
	}

	
}

/**********************************************************************************************/
/* Performs alpha-expansion for non regular grid graph for case when energy terms are        */
/* specified by a function */

void GCoptimization::set_up_expansion_energy_NG_FnPix(int size, LabelType alpha_label,Energy *e,Energy::Var *variables )
{
	Neighbor *tmp;
	int i,nPix,pix;
	


	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		m_lookupPixVar[pix] = i;


		if ( !m_neighbors[pix].isEmpty() )
		{
			m_neighbors[pix].setCursorFront();
			
			while ( m_neighbors[pix].hasNext() )
			{
				tmp = (Neighbor *) (m_neighbors[pix].next());
				nPix   = tmp->to_node;
				
				if ( m_labeling[nPix] != alpha_label )
				{
					if ( pix < nPix )
						e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
							          m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
									  m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
									  m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label),
									  m_smoothFnPix(pix,nPix,m_labeling[pix],m_labeling[nPix]));
				}
				else
					e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
						                       m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label));
				
			}
		}
	}
}

/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_ARRAY_VW(int size, LabelType alpha_label,Energy *e,
													  Energy::Var *variables )
{
	int i,nPix,pix,x,y;
	EnergyTermType weight;


	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		y = pix/m_width;
		x = pix - y*m_width;

		m_lookupPixVar[pix] = i;

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;
			weight = m_horizWeights[pix];
			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label)*weight,
							  m_smoothcost(alpha_label,m_labeling[nPix])*weight,
							  m_smoothcost(m_labeling[pix],alpha_label)*weight,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight);
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
				                 m_smoothcost(m_labeling[pix],alpha_label)*weight);
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
			weight = m_vertWeights[pix];
			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label)*weight ,
							  m_smoothcost(alpha_label,m_labeling[nPix])*weight,
							  m_smoothcost(m_labeling[pix],alpha_label)*weight ,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight );
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
				                 m_smoothcost(m_labeling[pix],alpha_label)*weight);
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*m_horizWeights[nPix],
			   	                 m_smoothcost(m_labeling[pix],alpha_label)*m_horizWeights[nPix]);
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,alpha_label)*m_vertWeights[nPix],
			   	                 m_smoothcost(m_labeling[pix],alpha_label)*m_vertWeights[nPix]);
		}	
			
	}
	
}





/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_ARRAY(int size, LabelType alpha_label,Energy *e,
													 Energy::Var *variables )
{
	int i,nPix,pix,x,y;


	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		y = pix/m_width;
		x = pix - y*m_width;

		m_lookupPixVar[pix] = i;

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label),
							  m_smoothcost(alpha_label,m_labeling[nPix]),
							  m_smoothcost(m_labeling[pix],alpha_label),
							  m_smoothcost(m_labeling[pix],m_labeling[nPix]));
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
				                 m_smoothcost(m_labeling[pix],alpha_label));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label) ,
							  m_smoothcost(alpha_label,m_labeling[nPix]),
							  m_smoothcost(m_labeling[pix],alpha_label) ,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix]) );
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
				                 m_smoothcost(m_labeling[pix],alpha_label));
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
			   	                 m_smoothcost(m_labeling[pix],alpha_label) );
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,alpha_label),
			   	                 m_smoothcost(m_labeling[pix],alpha_label));
		}	
			
	}
	
}

/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_ARRAY_VW_pix(int size, LabelType alpha_label,Energy *e,
													  Energy::Var *variables, PixelType *pixels, int num )
{
	int i,nPix,pix,x,y;
	EnergyTermType weight;


	for ( i = 0; i < num; i++ )
	{
		pix = pixels[i];
		if ( m_labeling[pix]!= alpha_label )
		{
			y = pix/m_width;
			x = pix - y*m_width;

			if ( x < m_width - 1 )
			{
				nPix = pix + 1;
				weight = m_horizWeights[pix];
				if ( m_labeling[nPix] != alpha_label && m_lookupPixVar[nPix] != -1 )
					e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label)*weight,
							  m_smoothcost(alpha_label,m_labeling[nPix])*weight,
							  m_smoothcost(m_labeling[pix],alpha_label)*weight,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight);
				else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
				                 m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight);
			}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
			weight = m_vertWeights[pix];
			if ( m_labeling[nPix] != alpha_label && m_lookupPixVar[nPix] != -1 )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label)*weight ,
							  m_smoothcost(alpha_label,m_labeling[nPix])*weight,
							  m_smoothcost(m_labeling[pix],alpha_label)*weight ,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight );
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
				                 m_smoothcost(m_labeling[pix],m_labeling[nPix])*weight);
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label || m_lookupPixVar[nPix] == -1)
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*m_horizWeights[nPix],
			   	                 m_smoothcost(m_labeling[pix],m_labeling[nPix])*m_horizWeights[nPix]);
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label ||	m_lookupPixVar[nPix] == -1)
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,alpha_label)*m_vertWeights[nPix],
			   	                 m_smoothcost(m_labeling[pix],m_labeling[nPix])*m_vertWeights[nPix]);
		}	
		}	
	}
	
}

/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_ARRAY_pix(int size, LabelType alpha_label,Energy *e,
													 Energy::Var *variables, PixelType *pixels,
													 int num)
{
	int i,nPix,pix,x,y;


	for ( i = 0; i < num; i++ )
	{
		pix = pixels[i];
		y = pix/m_width;
		x = pix - y*m_width;


		if ( m_labeling[pix]!= alpha_label )
		{
			if ( x < m_width - 1 )
			{
				nPix = pix + 1;

				if ( m_labeling[nPix] != alpha_label && m_lookupPixVar[pix] != -1)
					e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label),
							  m_smoothcost(alpha_label,m_labeling[nPix]),
							  m_smoothcost(m_labeling[pix],alpha_label),
							  m_smoothcost(m_labeling[pix],m_labeling[nPix]));
				else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
				                 m_smoothcost(m_labeling[pix],m_labeling[nPix]));
			}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;

			if ( m_labeling[nPix] != alpha_label && m_lookupPixVar[pix] != -1)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothcost(alpha_label,alpha_label) ,
							  m_smoothcost(alpha_label,m_labeling[nPix]),
							  m_smoothcost(m_labeling[pix],alpha_label) ,
							  m_smoothcost(m_labeling[pix],m_labeling[nPix]) );
			else   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
				                 m_smoothcost(m_labeling[pix],m_labeling[nPix]));
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label || m_lookupPixVar[nPix] == -1)
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
			   	                 m_smoothcost(m_labeling[pix],m_labeling[nPix]) );
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label || m_lookupPixVar[nPix] == -1)
			   e ->add_term1(variables[i],m_smoothcost(alpha_label,alpha_label),
			   	                 m_smoothcost(m_labeling[pix],m_labeling[nPix]));
		}	
			
	}
	}
}


/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_FnPix(int size, LabelType alpha_label,Energy *e,
													 Energy::Var *variables )
{
	int i,nPix,pix,x,y;


	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		y = pix/m_width;
		x = pix - y*m_width;

		m_lookupPixVar[pix] = i;

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
							  m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
							  m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label),
							  m_smoothFnPix(pix,nPix,m_labeling[pix],m_labeling[nPix]));
			else   e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
				                 m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_smoothFnPix(pix,nPix,alpha_label,alpha_label) ,
							  m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
							  m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label) ,
							  m_smoothFnPix(pix,nPix,m_labeling[pix],m_labeling[nPix]) );
			else   e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
				                 m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label));
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
			   	                 m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label) );
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
			   	                 m_smoothFnPix(pix,nPix,m_labeling[pix],alpha_label));
		}	
			
	}
	
}

/**********************************************************************************************/
/* Performs alpha-expansion for  regular grid graph for case when energy terms are NOT        */
/* specified by a function */
void GCoptimization::set_up_expansion_energy_G_FnCoord(int size, LabelType alpha_label,Energy *e,
													 Energy::Var *variables )
{
	int i,nPix,pix,x,y;


	for ( i = size - 1; i >= 0; i-- )
	{
		pix = m_lookupPixVar[i];
		y = pix/m_width;
		x = pix - y*m_width;

		m_lookupPixVar[pix] = i;

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_horz_cost(x,y,alpha_label,alpha_label),
							  m_horz_cost(x,y,alpha_label,m_labeling[nPix]),
							  m_horz_cost(x,y,m_labeling[pix],alpha_label),
							  m_horz_cost(x,y,m_labeling[pix],m_labeling[nPix]));
			else   e ->add_term1(variables[i],m_horz_cost(x,y,alpha_label,alpha_label),
				                 m_horz_cost(x,y,m_labeling[pix],alpha_label));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;

			if ( m_labeling[nPix] != alpha_label )
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
					          m_vert_cost(x,y,alpha_label,alpha_label) ,
							  m_vert_cost(x,y,alpha_label,m_labeling[nPix]),
							  m_vert_cost(x,y,m_labeling[pix],alpha_label) ,
							  m_vert_cost(x,y,m_labeling[pix],m_labeling[nPix]) );
			else   e ->add_term1(variables[i],m_vert_cost(x,y,alpha_label,alpha_label),
				                 m_vert_cost(x,y,m_labeling[pix],alpha_label));
		}	
		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_horz_cost(x-1,y,alpha_label,m_labeling[nPix]),
			   	                 m_horz_cost(x-1,y,m_labeling[pix],alpha_label) );
		}	

		if ( y > 0 )
		{
			nPix = pix - m_width;
	
			if ( m_labeling[nPix] == alpha_label )
			   e ->add_term1(variables[i],m_vert_cost(x,y-1,alpha_label,alpha_label),
			   	                 m_vert_cost(x,y-1,m_labeling[pix],alpha_label));
		}	
	}
}



/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::oneExpansionIteration()
{
	int next;
   
	terminateOnError( m_dataType == NONE,"You have to set up the data cost before running optimization");
	terminateOnError( m_smoothType == NONE,"You have to set up the smoothness cost before running optimization");

	if (m_random_label_order) scramble_label_table();
	

	for (next = 0;  next < m_num_labels;  next++ )
		perform_alpha_expansion(m_labelTable[next]);
	
	
	return(compute_energy());
}

/**************************************************************************************/

void GCoptimization::setNeighbors(PixelType pixel1, int pixel2, EnergyTermType weight)
{

	assert(pixel1 < m_num_pixels && pixel1 >= 0 && pixel2 < m_num_pixels && pixel2 >= 0);
	assert(m_grid_graph == 0);

	Neighbor *temp1 = (Neighbor *) new Neighbor;
	Neighbor *temp2 = (Neighbor *) new Neighbor;

	temp1->weight  = weight;
	temp1->to_node = pixel2;

	temp2->weight  = weight;
	temp2->to_node = pixel1;

	m_neighbors[pixel1].addFront(temp1);
	m_neighbors[pixel2].addFront(temp2);
	
}

/**************************************************************************************/

void GCoptimization::setNeighbors(PixelType pixel1, int pixel2)
{

	assert(pixel1 < m_num_pixels && pixel1 >= 0 && pixel2 < m_num_pixels && pixel2 >= 0);
	assert(m_grid_graph == 0);
	

	Neighbor *temp1 = (Neighbor *) new Neighbor;
	Neighbor *temp2 = (Neighbor *) new Neighbor;

	temp1->weight  = (EnergyTermType) 1;
	temp1->to_node = pixel2;

	temp2->weight  = (EnergyTermType) 1;
	temp2->to_node = pixel1;

	m_neighbors[pixel1].addFront(temp1);
	m_neighbors[pixel2].addFront(temp2);
	
}

/**************************************************************************************/

GCoptimization::~GCoptimization()
{

    // <!-- bagon
    // mexWarnMsgTxt("Calling destructor"); /* bagon added */
    if ( m_dataType == ARRAY )
        delete [] m_datacost;
    if ( m_smoothType == ARRAY )
        delete [] m_smoothcost;
    if ( m_varying_weights == 1 ) {
        delete [] m_vertWeights;
        delete [] m_horizWeights;
    }
    // bagon -->
    
	if ( m_deleteLabeling ) 
		delete [] m_labeling;


	if ( m_dataInput == SET_INDIVIDUALLY )
		delete [] m_datacost;

	if ( m_smoothInput == SET_INDIVIDUALLY )
			delete [] m_smoothcost;
 		
	if ( ! m_grid_graph )
		delete [] m_neighbors;			


	delete [] m_labelTable;
	delete [] m_lookupPixVar;
			
}


/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::swap(int max_num_iterations)
{
	return(start_swap(max_num_iterations)); 
}

/**************************************************************************************/


GCoptimization::EnergyType GCoptimization::swap()
{
	return(start_swap(MAX_INTT));
}

/**************************************************************************************/


GCoptimization::EnergyType GCoptimization::start_swap(int max_num_iterations )
{
	
	int curr_cycle = 1;
	EnergyType new_energy,old_energy;
	

	new_energy = compute_energy();

	old_energy = (new_energy+1)*10; // BAGON changed init value to exceed current energy by factor of 10 (thanks to A. Khan)    

	while ( old_energy > new_energy  && curr_cycle <= max_num_iterations)
	{
		old_energy = new_energy;
		new_energy = oneSwapIteration();
		
		curr_cycle++;	
	}

	return(new_energy);
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::oneSwapIteration()
{
	int next,next1;
   
	if (m_random_label_order) scramble_label_table();
		

	for (next = 0;  next < m_num_labels;  next++ )
		for (next1 = m_num_labels - 1;  next1 >= 0;  next1-- )
			if ( m_labelTable[next] < m_labelTable[next1] )
				perform_alpha_beta_swap(m_labelTable[next],m_labelTable[next1]);

	return(compute_energy());
}

/**************************************************************************************/

GCoptimization::EnergyType GCoptimization::alpha_beta_swap(LabelType alpha_label, LabelType beta_label)
{
	terminateOnError( alpha_label < 0 || alpha_label >= m_num_labels || beta_label < 0 || beta_label >= m_num_labels,
		"Illegal Label to Expand On");
	perform_alpha_beta_swap(alpha_label,beta_label);
	return(compute_energy());
}
/**************************************************************************************/

void GCoptimization::add_t_links_ARRAY_swap(Energy *e,Energy::Var *variables,int size,
											LabelType alpha_label, LabelType beta_label,
											PixelType *pixels)
{
	for ( int i = 0; i < size; i++ )
		e -> add_term1(variables[i], m_datacost(pixels[i],alpha_label),
									 m_datacost(pixels[i],beta_label));

}
	
/**************************************************************************************/

void GCoptimization::add_t_links_FnPix_swap(Energy *e,Energy::Var *variables,int size,
											LabelType alpha_label, LabelType beta_label,
											PixelType *pixels)
{
	for ( int i = 0; i < size; i++ )
		e -> add_term1(variables[i], m_dataFnPix(pixels[i],alpha_label),
									 m_dataFnPix(pixels[i],beta_label));

}
/**************************************************************************************/

void GCoptimization::add_t_links_FnCoord_swap(Energy *e,Energy::Var *variables,int size,
											  LabelType alpha_label, LabelType beta_label,
											  PixelType *pixels)
{
	int x,y;

	for ( int i = 0; i < size; i++ )
	{

		y = pixels[i]/m_width;
		x = pixels[i] - y*m_width;

		e -> add_term1(variables[i], m_dataFnCoord(x,y,alpha_label),m_dataFnCoord(x,y,beta_label));
	}
}


/**************************************************************************************/

void  GCoptimization::perform_alpha_beta_swap(LabelType alpha_label, LabelType beta_label)
{
	PixelType i,size = 0;
	Energy *e = new Energy(mexErrMsgTxt);
	PixelType *pixels = new PixelType[m_num_pixels];
	

	for ( i = 0; i < m_num_pixels; i++ )
	{
		if ( m_labeling[i] == alpha_label || m_labeling[i] == beta_label)
		{
			pixels[size]    = i;
			m_lookupPixVar[i] = size;
			size++;
		}
	}

	if ( size == 0 )
	{
		delete e;
		delete [] pixels;
		return;
	}


	Energy::Var *variables = (Energy::Var *) new Energy::Var[size];


	for ( i = 0; i < size; i++ )
		variables[i] = e ->add_variable();

	if ( m_dataType == ARRAY ) add_t_links_ARRAY_swap(e,variables,size,alpha_label,beta_label,pixels);
	else  if  ( m_dataType == FUNCTION_PIX ) add_t_links_FnPix_swap(e,variables,size,alpha_label,beta_label,pixels);
	else  add_t_links_FnCoord_swap(e,variables,size,alpha_label,beta_label,pixels);



	if ( m_grid_graph )
	{
		if ( m_smoothType == ARRAY )
		{
			if (m_varying_weights) set_up_swap_energy_G_ARRAY_VW(size,alpha_label,beta_label,pixels,e,variables);
			else set_up_swap_energy_G_ARRAY(size,alpha_label,beta_label,pixels,e,variables);
		}
		else if ( m_smoothType == FUNCTION_PIX ) set_up_swap_energy_G_FnPix(size,alpha_label,beta_label,pixels,e,variables);
		else  set_up_swap_energy_G_FnCoord(size,alpha_label,beta_label,pixels,e,variables);
			
	}
	else
	{
		if ( m_smoothType == ARRAY ) set_up_swap_energy_NG_ARRAY(size,alpha_label,beta_label,pixels,e,variables);
		else if ( m_smoothType == FUNCTION_PIX ) set_up_swap_energy_NG_FnPix(size,alpha_label,beta_label,pixels,e,variables);
	}
		

	e -> minimize();

	for ( i = 0; i < size; i++ )
		if ( e->get_var(variables[i]) == 0 )
			m_labeling[pixels[i]] = alpha_label;
		else m_labeling[pixels[i]] = beta_label;


	delete [] variables;
	delete [] pixels;
	delete e;

}

/**************************************************************************************/

void GCoptimization::set_up_swap_energy_NG_ARRAY(int size,LabelType alpha_label,LabelType beta_label,
												 PixelType *pixels,Energy* e, Energy::Var *variables)
{
	PixelType nPix,pix,i;
	EnergyTermType weight;
	Neighbor *tmp;
	


	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		if ( !m_neighbors[pix].isEmpty() )
		{
			m_neighbors[pix].setCursorFront();
			
			while ( m_neighbors[pix].hasNext() )
			{
				tmp = (Neighbor *) (m_neighbors[pix].next());
				nPix   = tmp->to_node;
				weight = tmp->weight;
				
				if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				{
					if ( pix < nPix )
						e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
							          m_smoothcost(alpha_label,alpha_label)*weight,
									  m_smoothcost(alpha_label,beta_label)*weight,
									  m_smoothcost(beta_label,alpha_label)*weight,
									  m_smoothcost(beta_label,beta_label)*weight);
				}
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
						                       m_smoothcost(beta_label,m_labeling[nPix])*weight);
			}
		}
	}
}

/**************************************************************************************/

void GCoptimization::set_up_swap_energy_NG_FnPix(int size,LabelType alpha_label,LabelType beta_label,
												 PixelType *pixels,Energy* e, Energy::Var *variables)
{
	PixelType nPix,pix,i;
	Neighbor *tmp;
	

	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		if ( !m_neighbors[pix].isEmpty() )
		{
			m_neighbors[pix].setCursorFront();
			
			while ( m_neighbors[pix].hasNext() )
			{
				tmp = (Neighbor *) (m_neighbors[pix].next());
				nPix   = tmp->to_node;
				
				if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				{
					if ( pix < nPix )
						e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
							          m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
									  m_smoothFnPix(pix,nPix,alpha_label,beta_label),
									  m_smoothFnPix(pix,nPix,beta_label,alpha_label),
									  m_smoothFnPix(pix,nPix,beta_label,beta_label) );
				}
				else
					e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
						                       m_smoothFnPix(pix,nPix,beta_label,m_labeling[nPix]));
			}
		}
	}
}

/**************************************************************************************/

void GCoptimization::set_up_swap_energy_G_FnPix(int size,LabelType alpha_label,LabelType beta_label,
												PixelType *pixels,Energy* e, Energy::Var *variables)
{
	PixelType nPix,pix,i,x,y;

	
	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		y = pix/m_width;
		x = pix - y*m_width;

		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
							  m_smoothFnPix(pix,nPix,alpha_label,beta_label),
							  m_smoothFnPix(pix,nPix,beta_label,alpha_label),
							  m_smoothFnPix(pix,nPix,beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
 					                       m_smoothFnPix(pix,nPix,beta_label,m_labeling[nPix]));
	
		}	
		if ( y > 0 )
		{
			nPix = pix - m_width;
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothFnPix(pix,nPix,alpha_label,alpha_label),
							  m_smoothFnPix(pix,nPix,alpha_label,beta_label),
							  m_smoothFnPix(pix,nPix,beta_label,alpha_label),
							  m_smoothFnPix(pix,nPix,beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
 					                       m_smoothFnPix(pix,nPix,beta_label,m_labeling[nPix]));
		}	

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
					e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
 					                           m_smoothFnPix(pix,nPix,beta_label,m_labeling[nPix]));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
				e ->add_term1(variables[i],m_smoothFnPix(pix,nPix,alpha_label,m_labeling[nPix]),
				                           m_smoothFnPix(pix,nPix,beta_label,m_labeling[nPix]));

		}
	}
}
/**************************************************************************************/

void GCoptimization::set_up_swap_energy_G_FnCoord(int size,LabelType alpha_label,LabelType beta_label,PixelType *pixels,
     											 Energy* e, Energy::Var *variables)
{  
	PixelType nPix,pix,i,x,y;

	
	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		y = pix/m_width;
		x = pix - y*m_width;

		if ( x > 0 )
		{
			nPix = pix - 1;
	
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_horz_cost(x-1,y,alpha_label,alpha_label),
							  m_horz_cost(x-1,y,alpha_label,beta_label),
							  m_horz_cost(x-1,y,beta_label,alpha_label),
							  m_horz_cost(x-1,y,beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_horz_cost(x-1,y,alpha_label,m_labeling[nPix]),
 					                           m_horz_cost(x-1,y,beta_label,m_labeling[nPix]));
	
		}	
		if ( y > 0 )
		{
			nPix = pix - m_width;
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_vert_cost(x,y-1,alpha_label,alpha_label),
							  m_vert_cost(x,y-1,alpha_label,beta_label),
							  m_vert_cost(x,y-1,beta_label,alpha_label),
							  m_vert_cost(x,y-1,beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_vert_cost(x,y-1,alpha_label,m_labeling[nPix]),
 					                       m_vert_cost(x,y-1,beta_label,m_labeling[nPix]));
		}	

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
					e ->add_term1(variables[i],m_horz_cost(x,y,alpha_label,m_labeling[nPix]),
 					                           m_horz_cost(x,y,beta_label,m_labeling[nPix]));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
				e ->add_term1(variables[i],m_vert_cost(x,y,alpha_label,m_labeling[nPix]),
				                           m_vert_cost(x,y,beta_label,m_labeling[nPix]));

		}
	}
}

/**************************************************************************************/

void GCoptimization::set_up_swap_energy_G_ARRAY_VW(int size,LabelType alpha_label,LabelType beta_label,
												   PixelType *pixels,Energy* e, Energy::Var *variables)
{
	PixelType nPix,pix,i,x,y;
	EnergyTermType weight;	



	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		y = pix/m_width;
		x = pix - y*m_width;

		if ( x > 0 )
		{
			nPix = pix - 1;
			weight = m_horizWeights[nPix];
	
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothcost(alpha_label,alpha_label)*weight,
							  m_smoothcost(alpha_label,beta_label)*weight,
							  m_smoothcost(beta_label,alpha_label)*weight,
							  m_smoothcost(beta_label,beta_label)*weight );
	
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
 					                       m_smoothcost(beta_label,m_labeling[nPix])*weight);
	
		}	
		if ( y > 0 )
		{
			nPix = pix - m_width;
			weight = m_vertWeights[nPix];

			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothcost(alpha_label,alpha_label)*weight,
							  m_smoothcost(alpha_label,beta_label)*weight,
							  m_smoothcost(beta_label,alpha_label)*weight,
							  m_smoothcost(beta_label,beta_label)*weight );
	
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*weight,
 					                       m_smoothcost(beta_label,m_labeling[nPix])*weight);
		}	

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*m_horizWeights[pix],
 					                           m_smoothcost(beta_label,m_labeling[nPix])*m_horizWeights[pix]);
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
				e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix])*m_vertWeights[pix],
				                           m_smoothcost(beta_label,m_labeling[nPix])*m_vertWeights[pix]);

		}
	}
}

/**************************************************************************************/

void GCoptimization::set_up_swap_energy_G_ARRAY(int size,LabelType alpha_label,LabelType beta_label,
											   PixelType *pixels,Energy* e, Energy::Var *variables)

{
	PixelType nPix,pix,i,x,y;
	


	for ( i = 0; i < size; i++ )
	{
		pix = pixels[i];
		y = pix/m_width;
		x = pix - y*m_width;

		if ( x > 0 )
		{
			nPix = pix - 1;
	
	
			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothcost(alpha_label,alpha_label),
							  m_smoothcost(alpha_label,beta_label),
							  m_smoothcost(beta_label,alpha_label),
							  m_smoothcost(beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
 					                       m_smoothcost(beta_label,m_labeling[nPix]));
	
		}	
		if ( y > 0 )
		{
			nPix = pix - m_width;

			if ( m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label)
				e ->add_term2(variables[i],variables[m_lookupPixVar[nPix]],
				              m_smoothcost(alpha_label,alpha_label),
							  m_smoothcost(alpha_label,beta_label),
							  m_smoothcost(beta_label,alpha_label),
							  m_smoothcost(beta_label,beta_label) );
	
				else
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
 					                       m_smoothcost(beta_label,m_labeling[nPix]));
		}	

		if ( x < m_width - 1 )
		{
			nPix = pix + 1;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label) )
					e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
 					                           m_smoothcost(beta_label,m_labeling[nPix]));
		}	

		if ( y < m_height - 1 )
		{
			nPix = pix + m_width;
	
			if ( !(m_labeling[nPix] == alpha_label || m_labeling[nPix] == beta_label))
				e ->add_term1(variables[i],m_smoothcost(alpha_label,m_labeling[nPix]),
				                           m_smoothcost(beta_label,m_labeling[nPix]));

		}
	}
}


/**************************************************************************************/

void GCoptimization::setLabelOrder(bool RANDOM_LABEL_ORDER)
{
	m_random_label_order = RANDOM_LABEL_ORDER;
}

/****************************************************************************/
/* This procedure checks if an error has occured, terminates program if yes */

void GCoptimization::terminateOnError(bool error_condition,const char *message)

{ 
   if  (error_condition) 
   {
       mexErrMsgIdAndTxt("GraphCut:internal_error","\nGCoptimization error: %s\n", message);
    }
}
