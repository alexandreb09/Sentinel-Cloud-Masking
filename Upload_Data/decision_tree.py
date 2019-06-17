from utils import startProgress, progress, endProgress
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
import seaborn as sns

import time

import os
currentdir = os.path.dirname(os.path.realpath(__file__))
os.path.dirname(currentdir)

sns.set()

def add_row(df, row):
    df.loc[-1] = row
    df.index = df.index + 1  
    return df.sort_index()


def load_file(filename, sheetname, show_time=True):
    """ Load an excel file
    Arguments:
        :param filename: 
        :param sheetname: 
        :param show_time=True:  show time loading took !
    """
    # read file
    t = time.time()
    df = pd.read_excel(filename, sheetname)
    if show_time:
        print("Dataset '%s' read in %3.2fs" % (sheetname, time.time() - t))

    return df


def get_train_test_dataset(df_training, df_evaluation, show_time=True):
    # Méthod (e.g. X dataset)
    cols_name_methods = df_training.columns[5:]

    # Select feature - output
    t = time.time()
    x_train = df_training[cols_name_methods].values
    y_train = (df_training["cloud"] * 1).values

    x_test = df_evaluation[cols_name_methods].values
    y_test = (df_evaluation["cloud"] * 1).values
    if show_time:
        print("Train - test dataset created in %3.2fs" % (time.time() - t))

    return x_train, x_test, y_train, y_test


def display_accuracy_over_nb_estimators(x_train, x_test, y_train, y_test, show_plot=True):
    times_fitting = []
    times_predict = []
    accuracies = []

    nb_estimators_list = [i for i in range(1, 10)] \
        + [i for i in range(10, 30, 2)] \
        + [i for i in range(30, 100, 5)] \
        + [i for i in range(100, 500, 10)] \

    startProgress("Compute accuracy vs number of estimators")
    for i, n_estimators in enumerate(nb_estimators_list):
        # Training
        t = time.time()

        regressor = RandomForestClassifier(
            n_estimators=n_estimators, random_state=0)

        # Fit model
        regressor.fit(x_train, y_train)
        times_fitting.append(time.time() - t)

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

    print("Best accuracy:\n", df[df.accuracies == max(df.accuracies)])
    #     nb_estimators_list  accuracies  times_fitting  times_predict
    # 18                  28     0.96645       0.428029       0.156244

    print("Worst accuracy:\n", df[df.accuracies == min(df.accuracies)])
    #    nb_estimators_list  accuracies  times_fitting  times_predict
    # 0                   1    0.965231       0.292976       0.109385

    if show_plot:
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


def plot_methods_prediction(res):
    # Sort by accuracy
    res = res.sort_values(by=["Accuracy"])

    # Plot
    sns.set_palette(reversed(sns.color_palette("Blues_d", res.shape[0])), res.shape[0])
    sns.barplot(data=res, x="Methods", y="Accuracy").set_title("Accuracy per method")

    # Add text value over each bar
    for i, (index, row) in enumerate(res.iterrows()):
        plt.text(x=i-0.3, y=row.Accuracy + 0.02,
                 s=round(row.Accuracy, 4), size=10)

    plt.xticks(rotation = 45)
    plt.show()


def decision_tree_accuracy(res, x_train, y_train, x_test, y_test):
    # Create Decision Tree classifer object
    tree = DecisionTreeClassifier()
    # Train Decision Tree Classifer
    tree = tree.fit(x_train, y_train)
    # Predict the response for test dataset
    y_pred = tree.predict(x_test)

    accuracy = accuracy_score(y_test, y_pred)
    add_row(res, ["decisionTree", accuracy])

    col_names = ['percentile1',
                 'percentile2', 'percentile3', 'percentile4', 'percentile5',
                 'persistence1', 'persistence2', 'persistence3', 'persistence4',
                 'persistence5', 'tree1', 'tree2', 'tree3']
    print(dict(zip(col_names, tree.feature_importances_)))

    return res


def random_forest_accuracy(res, x_train, y_train, x_test, y_test, n_estimators=28):
    # Create Decision Tree classifer object
    model_rf = RandomForestClassifier(n_estimators=n_estimators, random_state=0)
    # Fit model
    model_rf.fit(x_train, y_train)
    # Predict the response for test dataset
    y_pred = model_rf.predict(x_test)

    accuracy = accuracy_score(y_test, y_pred)
    add_row(res, ["randomForest", accuracy])

    print("Tree depths: ", [estimator.tree_.max_depth for estimator in model_rf.estimators_])

    return res
    

def linear_logistic_regression(res, x_train, y_train, x_test, y_test):
    from sklearn.linear_model import LogisticRegression
    # Create model
    model = LogisticRegression()
    # Fit model
    model.fit(x_train, y_train)
    # Predict the response for test dataset (proba output)
    y_pred = model.predict(x_test)
    # Categorize the output
    y_pred = np.where(y_pred > 0.5, 1, 0)

    accuracy = accuracy_score(y_test, y_pred)
    add_row(res, ["logisticRegression", accuracy])
    return res

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
    df_training = load_file("./Data/results.xlsx", "Training")
    df_evaluation = load_file("./Data/results.xlsx", "Evaluation")

    # Whole dataset
    df = df_training.append(df_evaluation)

    # Create an answer dataframe having the accuracy per method
    res = pd.DataFrame({"Methods": df.columns[5:],
                        "Accuracy": [accuracy_score(df.cloud, df[col]) for col in df.columns[5:]]})

    # Creating feature - output dataset
    x_train, x_test, y_train, y_test = get_train_test_dataset(df_evaluation, df_evaluation)

    # display_accuracy_over_nb_estimators(
    #     x_train, x_test, y_train, y_test, show_plot=True)

    # Run random Forest
    res = random_forest_accuracy(res, x_train, y_train, x_test, y_test)
    # Run decision tree
    res = decision_tree_accuracy(res, x_train, y_train, x_test, y_test)
    # Run logistic regression model
    linear_logistic_regression(res, x_train, y_train, x_test, y_test)

    print("Results:\n", res)
    plot_methods_prediction(res)
