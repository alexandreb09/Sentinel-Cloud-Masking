from IPython.display import Image
from subprocess import call
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# read file
df_training = pd.read_excel("./Data/results.xlsx", "Training")

# Méthod (e.g. X dataset)
cols_name_methods = df_training.columns[5:]
print("col name methods: ", cols_name_methods)

# Select feature - output
x = df_training[cols_name_methods].values
y = (df_training["cloud"] * 1).values

# Split training - evaluation dataset
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.15, random_state=0)

# Training
regressor = RandomForestClassifier(n_estimators=20, random_state=0)
# Fit model
regressor.fit(X_train, y_train)
# Evaluate model
y_pred = regressor.predict(X_test)

# Show precision
print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
print("Classification result:\n", classification_report(y_test, y_pred))
print("Accuracy: ", accuracy_score(y_test, y_pred))


from sklearn.tree import export_graphviz
# Export as dot file
export_graphviz(regressor.estimators_[5], out_file='randomForestTree.dot',
                feature_names= cols_name_methods,
                class_names = ["Cloudy", "Not Cloudy"],
                rounded=True, proportion=False,
                precision=2, filled=True)
# Convert to png using system command (requires Graphviz)
call(['dot', '-Tpng', 'D:\\Users\\AB43536\\Python\\GitHub\\Upload_Data\\randomForestTree.dot', '-o',
      'randomForestTree.png', '-Gdpi=600'])


# Display in jupyter notebook
# Image(filename= 'tree.png')
