#include <union_find.hpp>

UnionFind::UnionFind(size_t size_) : size(size_)
{
	parent = new size_t[size_];
	rank = new size_t[size_];

	for (size_t i = 0; i < size; ++i)
	{
		parent[i] = i;
		rank[i] = 0;
	}
}

UnionFind::~UnionFind()
{
	delete[] parent;
	delete[] rank;
}

void UnionFind::toSizeVector(std::vector<size_t> &vec, size_t &max)
{
	size_t *sizes = new size_t[size];
	for (size_t i = 0; i < size; ++i)
		sizes[i] = 0;
	for (size_t i = 0; i < size; ++i)
		sizes[findSet(i)]++;

	max = 0;
	vec.resize(size);
	for (size_t i = 0; i < size; i++)
	{
		vec[i] = sizes[findSet(i)];
		if (vec[i] > max) max = vec[i];
	}

	delete[] sizes;
}

void UnionFind::largestSet(std::vector<size_t>& result)
{
	size_t *sizes = new size_t[size];
	for (size_t i = 0; i < size; ++i)
		sizes[i] = 0;
	for (size_t i = 0; i < size; ++i)
		sizes[findSet(i)]++;

	size_t max = 0, max_idx = 0;
	for (size_t i = 0; i < size; ++i)
	{
		if (sizes[i] > max)
		{
			max = sizes[i];
			max_idx = i;
		}
	}

	delete[] sizes;

	result.clear();
	for (size_t i = 0; i < size; ++i)
	{
		if (findSet(i) == max_idx)
			result.push_back(i);
	}
}

void UnionFind::findSets(std::vector< std::vector<size_t> > &result, size_t thresh)
{
	std::vector< std::vector<size_t> > sets(size);
	for (size_t i = 0; i < size; ++i)
	{
		sets[findSet(i)].push_back(i);
	}

	for (size_t i = 0; i < size; ++i)
	{
		if (sets[i].size() >= thresh)
		{
			result.push_back(sets[i]);
		}
	}
}
