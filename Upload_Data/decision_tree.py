import pydot
from sklearn.tree import export_graphviz
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from matplotlib.legend_handler import HandlerLine2D
import seaborn as sns
import matplotlib.pyplot as plt

import time

import os
currentdir = os.path.dirname(os.path.realpath(__file__))
os.path.dirname(currentdir)

from utils import startProgress, progress, endProgress

def load_file(training_filename, training_sheetname, eval_filename, eval_sheetname, show_time=True):
    # read file
    t = time.time()
    df_training = pd.read_excel(training_filename, training_sheetname) # "./Data/results.xlsx", "Training")
    df_evaluation = pd.read_excel(eval_filename, eval_sheetname)  #"./Data/results.xlsx", "Evaluation")
    if show_time: print("Datasets read in %3.2fs" % (time.time() - t))

    return df_training, df_evaluation

def get_train_test_dataset(df_training, df_evaluation, show_time=True):
    # Méthod (e.g. X dataset)
    cols_name_methods = df_training.columns[5:]

    # Select feature - output
    t = time.time()
    x_train = df_training[cols_name_methods].values
    y_train = (df_training["cloud"] * 1).values

    x_test = df_evaluation[cols_name_methods].values
    y_test = (df_evaluation["cloud"] * 1).values
    if show_time: print("Train - test dataset created in %3.2fs" % (time.time() - t))
    
    return x_train, x_test, y_train, y_test


def display_accuracy_over_nb_estimators(x_train, x_test, y_train, y_test, show_plot=True):
    times_fitting = []
    times_predict = []
    accuracies = []

    nb_estimators_list = [i for i in range(1,10)] \
                            + [i for i in range(10, 30, 2)] \
                            + [i for i in range(30, 100, 5)] \
                            + [i for i in range(100, 500, 10)] \

    startProgress("Compute accuracy vs number of estimators")
    for i, n_estimators in enumerate(nb_estimators_list):
        # Training
        t = time.time()
        
        regressor = RandomForestClassifier(n_estimators=n_estimators, random_state=0)
        
        # Fit model
        regressor.fit(x_train, y_train)
        times_fitting.append( time.time() - t )

        # Evaluate model
        t = time.time()
        y_pred = regressor.predict(x_test)

        times_predict.append(time.time() - t)

        accuracies.append(accuracy_score(y_test, y_pred))

        progress(i/len(nb_estimators_list)*100)

    endProgress()

    df = pd.DataFrame({"nb_estimators_list": nb_estimators_list,
                       "accuracies": accuracies,
                       "times_fitting": times_fitting,
                       "times_predict": times_predict})

    print("Best accuracy:")
    print(df[df.accuracies == max(df.accuracies)])
    print("Worst accuracy:")
    print(df[df.accuracies == min(df.accuracies)])

    if show_plot:
        sns.set()

        fig = plt.figure()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        sns.lineplot(x="nb_estimators_list", y="accuracies", data=df, ax=ax1)
        sns.lineplot(x="nb_estimators_list",
                     y="times_fitting", data=df, ax=ax2)
        sns.lineplot(x="nb_estimators_list",
                     y="times_predict", data=df, ax=ax2)
        ax1.set_title("Accuracy over nb_estimators")
        ax2.set_title("Time over nb_estimators")
        ax2.legend(["times_fitting", "times_predict"], facecolor='w')

        plt.tight_layout()
        plt.show()

    return df




# # Training
# t = time.time()
# regressor = RandomForestClassifier(n_estimators=300, random_state=0)
# # Fit model
# regressor.fit(x_train, y_train)
# print("Model fitted in %3d" % (time.time() - t))

# # Evaluate model
# t = time.time()
# y_pred = regressor.predict(x_test)
# print("Model predicted in %3d" % (time.time() - t))

# # Show precision
# print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))
# print("Classification result:\n", classification_report(y_test, y_pred))
# print("Accuracy: ", accuracy_score(y_test, y_pred))


# # Save the tree as a png image
# export_graphviz(regressor.estimators_[0], out_file='tree.dot',
#                 feature_names=cols_name_methods,
#                 class_names=["Not Cloudy", "Cloudy"],
#                 rounded=True, precision=1)
# (graph, ) = pydot.graph_from_dot_file('tree.dot')
# graph.write_png('tree.png')


def number_tree_gain(x_test, y_test, x_train, y_train):
    from sklearn.metrics import roc_curve, auc

    # n_estimators = [1, 2, 4, 8, 16, 32, 64, 100, 200]
    n_estimators = [i for i in range(1, 200, 2)]

    train_results = []
    test_results = []
    for estimator in n_estimators:
        rf = RandomForestClassifier(n_estimators=estimator, n_jobs=-1)
        rf.fit(x_train, y_train)
        train_pred = rf.predict(x_train)

        false_positive_rate, true_positive_rate, thresholds = roc_curve(
            y_train, train_pred)
        roc_auc = auc(false_positive_rate, true_positive_rate)
        train_results.append(roc_auc)
        y_pred = rf.predict(x_test)
        false_positive_rate, true_positive_rate, thresholds = roc_curve(
            y_test, y_pred)
        roc_auc = auc(false_positive_rate, true_positive_rate)
        test_results.append(roc_auc)

    line1, = plt.plot(n_estimators, train_results, "b", label="Train AUC")
    line2, = plt.plot(n_estimators, test_results, 'r', label="Test AUC")
    plt.legend(handler_map={line1: HandlerLine2D(numpoints=2)})
    plt.ylabel('AUC score')
    plt.xlabel('n_estimators')
    plt.show()


if __name__ == "__main__":
    df_training, df_evaluation = load_file(
        "./Data/results.xlsx", "Training", "./Data/results.xlsx", "Evaluation")

    x_train, x_test, y_train, y_test = get_train_test_dataset(df_evaluation, df_evaluation)

    display_accuracy_over_nb_estimators(
        x_train, x_test, y_train, y_test, show_plot=True)
