import graphviz
from sklearn import tree
from sklearn.tree import export_graphviz                # Export tree to graphviz
import pandas as pd                                     # Load data as data frame
import h5py                                             # Read .h5 file
from sklearn.tree import DecisionTreeClassifier, export_graphviz   # Decision tree builder + display Decision Tree 
import subprocess                                       # Run subprocess for creating graphviz
import numpy as np

number_rows_kept = 1000
training_ratio = 0.8

bands_name = ["B" + bd.decode("utf-8")
              for bd in f["band"]]             # Decode bands names
class_names = [name.decode("utf-8")
               for name in f["class_names"]]       # Decode class names

# Loading data - read file
with h5py.File('20170412_s2_manual_classification_data.h5', 'r') as f:
    keys = list(f.keys())                  # Get keys from file
    # Load features (bands 1 to 12)
    features_dataset = f["spectra"][:number_rows_kept]
    # Load target classes
    targets_dataset = f["classes"][:number_rows_kept]
    longitude = f["longitude"][:number_rows_kept]
    lattitude = f["lattitude"][:number_rows_kept]

number_of_row = targets_dataset.shape[0]

def getSamplingVector(size, frac):
    """
    Return a boolean vector with a frac pourcentage of True values in
    Arguments
        :param size: size of the return vetor 
        :param frac: number of True in the return vector
    """
    rep = np.full((size), False)
    for i in range(int(size * frac)):
        rep[i] = True
    np.random.shuffle(rep)
    return rep

sampling_vector = getSamplingVector(number_of_row, training_ratio)

targets_training = targets_dataset[sampling_vector]
targets_evaluate = targets_dataset[sampling_vector == False]

feature_training = features_dataset[sampling_vector]
feature_evaluate = features_dataset[sampling_vector == False]

print(keys)
def printClassNames():
    print("\nid names")
    for id, name in zip(f['class_ids'], f['class_names']):
        print("%2d %s" % (id, name.decode("utf-8")))


print(f["cite"].value)
print(f["cite"].shape)

def runDecisionTree(features, targets):
    """
    Return a decision tree trained
    Arguments
        :param features: 
        :param targets: 
    """
    dtree = tree.DecisionTreeClassifier()
    dtree.fit(features, targets)
    return dtree


def saveTreeAsPdf(dtree, bands_name, class_names, filename="Decision tree"):
    """
    Export decision tree to a PDF file
        :param dtree: 
        :param bands_name: 
        :param class_names: 
        :param filename="Decisiontree": 
    """
    dot_data = tree.export_graphviz(dtree, out_file=None,
                                    feature_names=bands_name,
                                    class_names=class_names,
                                    filled=True, rounded=True,
                                    special_characters=True,)
    graph = graphviz.Source(dot_data)
    graph.render("Decision tree clouds")

"""
def unGzFile():
    # python 3

    # decompress a gzip file
    import gzip

    input = gzip.GzipFile("pyGTiff-1.0.3.tar.gz", 'rb')
    s = input.read()
    input.close()

    output = open("pyGTiff-1.0.3.tar", 'wb')
    output.write(s)
    output.close()

    print("done")
"""
