#ifndef FW_HEADER_H_
#define FW_HEADER_H_

enum GrpType{
	SHADE,
	REF
};


///basic unit
struct Element{
	int m_eleID; //element ID
	cv::Vec3f m_rgb;
	float m_conf; //element confidence(importance)
	Element(int id, float conf)
	:m_eleID(id)
	,m_conf(conf)
	{
		
	}
};
///used to sort element
struct EleGreater{
	bool operator()(const Element& e1, const Element& e2){
		return e1.m_conf > e2.m_conf;
	}
};

///element grouping relationship
struct GrpEle{
	int m_gID; //group ID
	GrpType m_grpType; //group type, Element might have different group types simutaneoulsy
	int m_solution; //solution
	std::vector<Element> m_eMember; //element members
};

struct EleGrp{
	int m_eID; //element ID
	std::vector<Element> m_gMember; //group members
	int m_mcShadingGrpIdx;
	int m_mcRefGrpIdx;
	int m_mcShadingVectPos;
	int m_mcRefVectPos;

};

typedef std::vector<GrpEle> grpEle_vect; //also nodes
typedef std::vector<EleGrp> eleGrp_vect;


#endif /*FW_HEADER_H_*/
