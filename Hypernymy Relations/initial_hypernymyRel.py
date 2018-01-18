import pickle
import requests
from tqdm import tqdm

import pprint
pp = pprint.PrettyPrinter(indent=2)

def preprocess(line):
	return line.replace(' ','_')[:-1]

def prettyPrint(phrase):
	# pp.pprint(results["python"])  #for full json response
	for relation in results[phrase]:
		start = relation['start']['label'].lower()
		rel = relation['rel']['label']
		end = relation['end']['label'].lower()
		weight = relation['weight']
		if rel == "IsA" and start == phrase:
			print (str(weight)+": "+start+"-->"+rel+"-->"+end)

def get_init_relations():
	results = {}
	noFind = 0
	listOfPhrases = open("../moocs_tags", "r")
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
	pickle_out = open("cn_edges.pickle","wb")
	pickle.dump(results, pickle_out)
	pickle_out.close()

def get_more_relations(results, listOfPhrases):
	noFind = 0
	for line in tqdm(listOfPhrases):
		if line[:-1] not in results:
			search_phrase = preprocess(line)
			try:
				obj = requests.get('http://api.conceptnet.io/c/en/'+search_phrase+"?offset=0&limit=100000").json()
				x = obj['edges'][0]
				results[line[:-1]] = obj['edges']
			except IndexError:
				noFind += 1
				print (str(noFind)+" "+line)
	print (noFind)
	return results

### Load tags and create pickle 
# get_init_relations()


results = {}
pickle_in = open("cn_edges.pickle","rb")
results = pickle.load(pickle_in)

# prettyPrint("python")

IsA_dict = {}
IsA_rev = {}

for key, value in results.items():
	for relation in value:
		start = relation['start']['label'].lower()
		rel = relation['rel']['label']
		end = relation['end']['label'].lower()
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

# pp.pprint(IsA_rev)  #for full json response

temp = {}
for key in list(IsA_rev.keys()):
	if len(IsA_rev[key])>1:
		temp[key] = IsA_rev[key]

pp.pprint(temp)
