import pickle
import requests
from tqdm import tqdm


############################# PREPROCESSING FUNCTIONS + HELPERS #############################

## Pretty Printing JSONs
import pprint
pp = pprint.PrettyPrinter(indent=2)
def prettyPrint(phrase):
	# pp.pprint(results["python"])  #for full json response
	for relation in results[phrase]:
		start = relation['start']['label'].lower()
		rel = relation['rel']['label']
		end = relation['end']['label'].lower()
		weight = relation['weight']
		if rel == "IsA" and start == phrase:
			print (str(weight)+": "+start+"-->"+rel+"-->"+end)

## Text Pre-Processing

# This function splits the line on ':', runs the spelling fixer, removes punctuation (including hashtags) from the start of sentence, replaces all spaces with underscores in order to query the ConceptNet API and drops the end line character.
def preprocess(line):
	if ":" in line:
		line = line.split(':')[0]
	while line[0] in string.punctuation:
		line = line[1:]
	line = line.replace("\,", ",")
	line = spellFixer(line)
	return line.replace(' ','_')[:-1]

# Replaces all spaces with underscores for querying ConceptNetAPI
def preprocess_hypernyms(line):
	return line.replace(' ','_')

# This function fixes the spelling of words that are incorrectly spelt.
import enchant
import editdistance
def spellFixer(phrase):
	words = phrase.split(' ')
	d = enchant.Dict("en_US")
	fixed_phrase = ""
	for word in words:
		if len(word) > 0 and d.check(word):
			fixed_phrase+=word
			fixed_phrase+=" "
		else:
			try:
				newp = min(d.suggest(word), key=lambda x: editdistance.eval(word, x))
				fixed_phrase+=newp
				fixed_phrase+=" "
			except ValueError:
				fixed_phrase+=word
				fixed_phrase+=" "
	return fixed_phrase[:-1]

############################# QUERYING FUNCTIONS + HELPERS #############################

# This functions gets relations from conceptnet and stores in pickle
def get_init_relations(tags, filename):
	results = {}
	noFind = 0
	listOfPhrases = open(tags, "r")
	for line in tqdm(listOfPhrases):
		search_phrase = preprocess(line)
		try:
			obj = requests.get('http://api.conceptnet.io/c/en/'+search_phrase+"?offset=0&limit=100000").json()
			x = obj['edges'][0]
			results[line[:-1]] = obj['edges']
		except IndexError:
			noFind += 1
			print (str(noFind)+" "+line)
	print (noFind)
	pickle_out = open(filename,"wb")
	pickle.dump(results, pickle_out)
	pickle_out.close()
	return results

# This function is called when we want to find the relations for hypernyms and stores in pickle
def get_more_relations(hypernyms, filename, results):
	newResults = {}
	noFind = 0
	phrases = list(set(hypernyms) - set(results.keys()))
	for line in tqdm(phrases):
		if line[:-1] not in results:
			search_phrase = preprocess_hypernyms(line)
			try:
				obj = requests.get('http://api.conceptnet.io/c/en/'+search_phrase+"?offset=0&limit=100000").json()
				x = obj['edges'][0]
				newResults[line] = obj['edges']
			except IndexError:
				noFind += 1
				# print (str(noFind)+" "+line)
	print (noFind, " not found")
	pickle_out = open(filename,"wb")
	pickle.dump(newResults, pickle_out)
	pickle_out.close()
	return newResults

############################# CLUSTERING FUNCTIONS + HELPERS #############################

# This function computes the clusters
def computeClusters(results):
	IsA_dict = {}
	IsA_rev = {}

	for key, value in results.items():
		for relation in value:
			start = relation['start']['label'].lower()
			rel = relation['rel']['label']
			end = relation['end']['label'].lower()
			if end[:2] == "a ":
				end = end[2:]
			if end[:3] == "an ":
				end = end[3:]
			weight = relation['weight']
			if start == key and rel == "IsA" and weight>1:
				# print (str(weight) + ":   " + start+"-->"+rel+"-->"+end)
				try:
					IsA_dict[start].append(end)
				except KeyError:
					IsA_dict[start] = [end]
				try:
					IsA_rev[end].append(start)
				except KeyError:
					IsA_rev[end] = [start]
	print ("Clusters computed")
	return IsA_rev,IsA_dict


# This function merges clusters
def leafMerge(l1Cluster):
	# trying to merge leaves incase they are in upper layer, e.g. 'physics-> nuclear physics' and 'science->physics' you get 'science -> nuclear physics'
	flag = True
	l2Cluster = l1Cluster.copy()
	j = 1
	while flag:
		j+=1
		i = 1
		for key, value in l2Cluster.items():
			# print(i,"/",len(l2Cluster.keys()),key)
			i +=1
			for concept in value:
				if concept in list(l1Cluster.keys()):
					# print (key, l2Cluster[key])
					l2Cluster[key].remove(concept)
					# print (len(l2Cluster[concept]), "--", l2Cluster[concept])
					l2Cluster[key] = l2Cluster[key] + l2Cluster[concept]
					# print (key, l2Cluster[key])
					# print ("------------------------------------------------------")
		if (l1Cluster == l2Cluster):
			flag = False
		l1Cluster = l2Cluster.copy()
	return l2Cluster

#Remove duplicates in a cluster after merging
def removeDuplicates(clusters):
	c = clusters.copy()
	for key, value in c.items():
		clusters[key] = list(set(value))
	return clusters

# This function drop all clusters that are total sub clusters and empty clusters
def drop_FullClusterOverlap(IsA_rev,mergedCluster):
	original = IsA_rev.copy()
	mCluster = mergedCluster.copy()
	for oKey, oValue in original.items():
		for mkey, mvalue in mCluster.items():
			if all(x in mvalue for x in oValue) and not set(oValue) == set(mvalue):
				mergedCluster.pop(oKey, None)
	return mergedCluster

# This funtion removes clusters which have only one concept
def dropClustersWithOneConcept(clusters):
	temp = {}
	for key in list(clusters.keys()):
		if len(clusters[key])>1:
			temp[key] = clusters[key]
	return temp

############################# MULTI-LEVEL CLUSTERING FUNCTIONS + HELPERS #############################

# This helper function concats all the lists that are values in a dict
def aggValues(hyper):
	l = []
	for k,v in hyper.items():
		for i in v:
			l.append(i)
	return list(set(l))


# This function is used when level-ing up our hypernym relations
def levelUpClusters(hyperClusters, hypo):
	hyper = hyperClusters.copy()

	#First we drop clusters with only one concept
	hyper = dropClustersWithOneConcept(hyper)
	
	#Next we keep track of which keys from the hyponyms did not appear anywhere in the dict of hypernyms.
	temp = {}
	for key in list(hypo.keys()):
		if key not in aggValues(hyper):
			temp[key] = hypo[key]

	#Next we level up all our original clusters into their new clusters
	for key, value in hyper.items():
		for concept in value:
			if concept in list(hypo.keys()):
				hyper[key].remove(concept)
				hyper[key] = hyper[key] + hypo[concept]

	#Finally we merge in all the clusters that went missing when we created the higher level clusters
	hyper = {**hyper, **temp}
	return hyper


############################# EXECUTION CODE #############################

# # Load tags and store in pickle
# tags = "../moocs_tags"
# get_init_relations(tags,"cn_edges.pickle")

# Load tags from pickle
results = {}
pickle_one = open("cn_edges.pickle","rb")
results = pickle.load(pickle_one)

def singleLevelClustering(results):
	# Compute initial clusters
	IsA_rev,IsA_dict = computeClusters(results)

	# # Merge clusters
	dropped = drop_FullClusterOverlap(IsA_rev,IsA_rev.copy())
	mergedCluster = removeDuplicates(leafMerge(dropped.copy()))
	final = drop_FullClusterOverlap(IsA_rev,mergedCluster.copy())
	return final

single_level_clusters = singleLevelClustering(results)
final_single = dropClustersWithOneConcept(single_level_clusters) #### Output this if you want results after single level of hypernym relations
print ("single clusters: ", len(list(final_single.keys())))
pp.pprint(final_single)

print("--------------------------------------------------------------------------------------------------")
#### From this point on the code is getting the multi-level relations to get more broader clusters ########




# print ("Getting Hypernym relations")
# # Load more tags and store in pickle
# new_results = get_more_relations(list(single_level_clusters.keys()),"cn_edges_plus.pickle", results)

# Read new tags from pickle
new_results = {}
pickle_two = open("cn_edges_plus.pickle","rb")
new_results = pickle.load(pickle_two)


def multiLevelClustering(new_results, single_level_clusters):
	new_IsA_rev,new_IsA_dict = computeClusters(new_results)
	clusters = levelUpClusters(new_IsA_rev, single_level_clusters)
	mergedCluster = removeDuplicates(leafMerge(clusters.copy()))
	final = drop_FullClusterOverlap(clusters,mergedCluster.copy())
	return final

multi_level_clusters = multiLevelClustering(new_results, single_level_clusters)
final_multi = dropClustersWithOneConcept(multi_level_clusters)
print ("multi clusters: ", len(list(final_multi.keys())))
pp.pprint(final_multi)


