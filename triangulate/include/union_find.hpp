#ifndef __CORE_UNION_FIND_H
#define __CORE_UNION_FIND_H

#include <cstring>
#include <vector>
#include <stdexcept>

/**
 * General union-find for merging disjoint sets (thread unsafe).  NONE of the
 * operations are thread-safe.
 *
 * There are thread-safe versions out there, but this runs plenty fast already.
 * In practice, gathering the data (e.g. point cloud neighbors to send to
 * UnionFind) is slower than any of UnionFind's functions, so optimization is
 * not worth it.
 */
class UnionFind
{
public:
	UnionFind(size_t size_);
	~UnionFind();

	// combine the sets containing x and y
	inline void unionSets(size_t x, size_t y)
	{
		if (x >= size || y >= size) throw new std::range_error("unionSets index out of bounds");

		const size_t xroot = findSet(x);
		const size_t yroot = findSet(y);
		if (xroot == yroot)
		{
			return;
		}

		if (rank[xroot] < rank[yroot])
		{
			parent[xroot] = yroot;
		}
		else if (rank[xroot] > rank[yroot])
		{
			parent[yroot] = xroot;
		}
		else
		{
			parent[yroot] = xroot;
			rank[xroot]++;
		}
	}

	// find the set that x belongs to
	// use full path compression
	inline size_t findSet(size_t x)
	{
		if (x >= size) throw new std::range_error("findSet index out of bounds");

		// naive path compression:

		// if (parent[x] != x) {
		//    parent[x] = findSet(parent[x]);
		// }
		// return parent[x];

		// optimized path compression:

		size_t y = parent[x];
		if (y == x)
			return x;

		// check if x's parent is already root
		size_t r = y;
		size_t p = parent[r];
		if (p == r)
			return r;

		// traverse with r to root
		do
		{
			r = p;
			p = parent[r];
		}
		while (r != p);

		// assign all nodes along chain to root (r), traverse with r
		parent[x] = r;
		p = parent[y];
		do
		{
			parent[y] = r;
			y = p;
			p = parent[y];
		}
		while (p != r);

		return r;
	}

	// sets every component of vec equal to the size of its cluster
	// and returns the max
	void toSizeVector(std::vector<size_t> &vec, size_t & max);

	// finds the set with the most elements.  ties are broken arbitrarily.
	void largestSet(std::vector<size_t> &result);

	// finds all sets with at least thresh elements in them
	void findSets(std::vector< std::vector<size_t> > &result, size_t thresh = 3);

private:
	size_t* parent;
	size_t* rank;
	const size_t size;
};

#endif
