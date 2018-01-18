import pickle, sys
import text2uri as t2u
import matplotlib.pyplot as plt

import numpy as np

from scipy.cluster.vq import whiten, kmeans2

with open('vectorDict.pickle','rb') as handle:
	vectorDict1 = pickle.load(handle)

with open('vectorDict2.pickle','rb') as handle:
	vectorDict2 = pickle.load(handle)


vectorDict = {**vectorDict1, **vectorDict2}

print ("loaded")

with open("../moocs_tags", "r") as f:
    content = f.readlines()

vec_list = []
noMatch = 0
for x in content:
	try:
		y = vectorDict[t2u._standardized_text(x,t2u.english_filter)]
		vec_list.append([float(x) for x in y])
	except:
		noMatch+=1
		pass
		#modify x
				

print (len(vec_list))
print (noMatch)

vector_array = np.array(vec_list, np.float32)
whitened = whiten(vector_array)





# # determine k using elbow method

# from sklearn.cluster import KMeans
# from sklearn import metrics
# from scipy.spatial.distance import cdist
# import numpy as np
# import matplotlib.pyplot as plt


# # create new plot and data
# plt.plot()
# X = whitened.reshape(len(vec_list[0]), len(vec_list))
# colors = ['b', 'g', 'r']
# markers = ['o', 'v', 's']

# # k means determine k
# distortions = []
# K = range(1,250,10)
# for k in K:
#     print(k)
#     kmeanModel = KMeans(n_clusters=k).fit(X)
#     kmeanModel.fit(X)
#     distortions.append(sum(np.min(cdist(X, kmeanModel.cluster_centers_, 'jaccard'), axis=1)) / X.shape[0])

# # Plot the elbow
# plt.plot(K, distortions, 'bx-')
# plt.xlabel('k')
# plt.ylabel('Distortion')
# plt.title('The Elbow Method showing the optimal k')
# plt.show()

















# clustering dataset


codebook, label = kmeans2(whitened, 100, iter=100, thresh=1e-05, minit='points', missing='warn', check_finite=True)
# kmeans(whitened, 2,iter=20,threhs=1e-05)

clusters = []
for i in codebook:
	clusters.append([])

for x in content:
	try:
		mindist = float('Inf')
		small = float('NaN')
		y = vectorDict[t2u._standardized_text(x,t2u.english_filter)]
		row = [float(x) for x in y]
		for idx,centroid in enumerate(codebook):
			dist = np.linalg.norm(centroid-np.asarray(row))
			print (small, dist, mindist)
			if dist < mindist:
				mindist = dist
				small = idx
			print (small, dist, mindist)
			print ("---------")
		clusters[small].append(x.strip())
	except KeyError:
		pass

print (clusters)