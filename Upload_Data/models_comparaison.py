from utils import startProgress, progress, endProgress, add_row
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier, export_graphviz
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.linear_model import LogisticRegression

import matplotlib.pyplot as plt
from matplotlib.legend_handler import HandlerLine2D
import seaborn as sns
import pydot
import time

import os
currentdir = os.path.dirname(os.path.realpath(__file__))
os.path.dirname(currentdir)

# Bigger than normal fonts
sns.set(font_scale=1.7)


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


def split_feature_output(df, feature_names, show_time=True):
    """ Split a dataset in feature dataset and output column
    docstring here
        :param df: dataframe to split
        :param feature_names: 
        :param show_time=True: 
    """
    # Select feature - output
    t = time.time()
    x = df[feature_names].values
    y = (df["cloud"] * 1).values

    if show_time:
        print("Train - test dataset created in %3.2fs" % (time.time() - t))

    return x, y


def compute_accuracy_over_nb_estimators(x_train, x_test, y_train, y_test,
                                        show_plot=True, progress_bar=True):
    times_fitting = []
    times_predict = []
    accuracies = []

    nb_estimators_list = [i for i in range(1, 10)] \
        + [i for i in range(10, 30, 2)] \
        + [i for i in range(30, 100, 5)] \
        + [i for i in range(100, 500, 10)] \
    
    if progress_bar: startProgress("Compute accuracy vs number of estimators")
    
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

        if progress_bar: progress(i/len(nb_estimators_list)*100)

    if progress_bar: endProgress()

    df = pd.DataFrame({"nb_estimators_list": nb_estimators_list,
                       "accuracies": accuracies,
                       "times_fitting": times_fitting,
                       "times_predict": times_predict})

    # print("Best accuracy:\n", df[df.accuracies == max(df.accuracies)])
    #     nb_estimators_list  accuracies  times_fitting  times_predict
    # 18                  28     0.96645       0.428029       0.156244

    # print("Worst accuracy:\n", df[df.accuracies == min(df.accuracies)])
    #    nb_estimators_list  accuracies  times_fitting  times_predict
    # 0                   1    0.965231       0.292976       0.109385

    if show_plot:
        plot_accuracy_over_nb_estimatros(df)

    return df

def plot_accuracy_over_nb_estimatros(df):
    """ Plot the accuracy - time_splitting - time_evaluation over the nb_estimatros 
    Arguments
        :param df: dataframe with : [nb_estimators_list,times_fitting, times_predict]
    """
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

def plot_accuracy_over_methods(res):
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


def plot_methods_repartition(data, feature_names):
    # Select feature + output columns
    data = data[["cloud"] + feature_names]

    # Figure size
    plt.rcParams["figure.figsize"] = (20, 10)

    # Count the number of 0 and 1
    # Return a list = [sum of 0, sum of 1]
    def get_sum(col):
        return [sum(col == 0), sum(col == 1)]

    # Compute the number of 0 and 1 per column + transformation for seaborn plot
    res = data.apply(get_sum, axis=0).to_frame()
    res = pd.DataFrame(res[0].values.tolist(), columns=[
                    "Cloud", "Not cloud"], index=res.index).stack().to_frame()
    res.reset_index(inplace=True)
    res = res.set_axis(['Method', 'Cloud ?', 'Count'], axis=1, inplace=False)

    # Create plot
    sns.barplot(x="Method", y="Count", hue="Cloud ?", data=res).set_title(
        'Distribution of prediction methods')
    plt.xticks(rotation=30)

    plt.show()


def accuracy_over_number_of_feature(training, evaluation, feature_names, n_estimators):
    """ Compute the accuracy by decreasing the number of feature column
     (removing the less important feature at each iteration)
    docstring here
        :param training: 
        :param evaluation: 
        :param n_estimators: 
    """
    res = pd.DataFrame({"Number_of_features": [i for i in range(len(feature_names), 0, -1)],
                        "Accuracy": [-1 for i in range(len(feature_names), 0 , -1)]})
    
    feat_col = feature_names.copy()

    for nb_features in res.Number_of_features:
        # Create Decision Tree classifer object
        model_rf = RandomForestClassifier(n_estimators=n_estimators, random_state=0)
        # Fit model
        model_rf.fit(training[feat_col], training.cloud)
        # Predict the response for test dataset
        y_pred = model_rf.predict(evaluation[feat_col])

        # Compute accuracy
        accuracy = accuracy_score(evaluation.cloud, y_pred)
        res.loc[res.Number_of_features == nb_features, 'Accuracy'] = accuracy

        # Remove less important variables
        del feat_col[np.argmin(model_rf.feature_importances_)]

    return res

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


def feature_importance_per_model(training, evaluation, features, nb_estimators=500):
    results = pd.DataFrame(columns=["Methods", "Importance", "Model_id", "Accuracy"])

    # List of features kept
    for index, feature_to_remove in enumerate([""] + features):
        # Create copy
        feature_names = features.copy()
        # Remove the current feature
        if feature_to_remove in feature_names:
            feature_names.remove(feature_to_remove)

        # Subset the datasets
        sub_training = training[["cloud"] + feature_names]
        sub_evaluation = evaluation[["cloud"] + feature_names]
        # Creating feature - output dataset
        x_train, y_train = split_feature_output(sub_training, feature_names, show_time=False)
        x_test, y_test = split_feature_output(sub_evaluation, feature_names, show_time=False)

        # Create Decision Tree classifer object
        model_rf = RandomForestClassifier(n_estimators=nb_estimators, random_state=0)
        # Fit model
        model_rf.fit(x_train, y_train)
        # Eval the model
        y_pred = model_rf.predict(x_test)

        accuracy = accuracy_score(y_test, y_pred)

        current_res = pd.DataFrame({"Methods": feature_names,
                                    "Importance": model_rf.feature_importances_,
                                    "Model_id": [index for i in feature_names],
                                    "Accuracy": [accuracy for _ in feature_names],
                      })

        results = results.append(current_res)
    return results.reset_index(drop=True)


def plot_feature_importance_per_model(df, features):
    """ plot feature importance per model
    Arguments:
        :param df: results dataframe from feature_importance_per_model() method
        :param features: feature names used in feature_importance_per_model() method
    """
    colors = {"tree3": "#F26419",
              "tree2": "#F6AE2D",
              "tree1": "#33658A",
              "percentile1": "#86BBD8",
              "percentile5": "#2F4858"}

    fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(15, 15))
    fig.subplots_adjust(hspace=0.5)
    fig.suptitle('Features importance')

    for ax, grouped in zip(axes.flatten(), df.groupby("Model_id")):
        data = grouped[1]
        palette = [colors[key] for key in data.Methods]
        sns.barplot(x='Methods', y='Importance', data=data, ax=ax, palette=palette)
        

        title = 'Accuracy: {:06.3f}%'.format(data.iloc[0]["Accuracy"]*100)
        if data.shape[0] == 5:
            title
        
        ax.title.set_text(title)
        plt.sca(ax)
        plt.xticks(rotation=90)

    plt.show()



def plot_precision_recall_vs_threshold(precisions, recalls, thresholds):
    """
    Modified from:
    Hands-On Machine learning with Scikit-Learn
    and TensorFlow; p.89
    """
    plt.figure(figsize=(8, 8))
    plt.title("Precision and Recall Scores as a function of the decision threshold")
    plt.plot(thresholds, precisions[:-1], "b--", label="Precision")
    plt.plot(thresholds, recalls[:-1], "g-", label="Recall")
    plt.ylabel("Score")
    plt.xlabel("Decision Threshold")
    plt.legend(loc='best')


def plot_roc_curve(fpr, tpr, label=None):
    """
    The ROC curve, modified from 
    Hands-On Machine learning with Scikit-Learn and TensorFlow; p.91
    """
    plt.figure(figsize=(8, 8))
    plt.title('ROC Curve')
    plt.plot(fpr, tpr, linewidth=2, label=label)
    plt.plot([0, 1], [0, 1], 'k--')
    plt.axis([-0.005, 1, 0, 1.005])
    plt.xticks(np.arange(0, 1, 0.05), rotation=90)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate (Recall)")
    plt.legend(loc='best')
'''
if __name__ == "__main__":
    df_training = load_file("./Data/results.xlsx", "Training")
    df_evaluation = load_file("./Data/results.xlsx", "Evaluation")

    # Whole dataset
    df = df_training.append(df_evaluation)

    # Create an answer dataframe having the accuracy per method
    res = pd.DataFrame({"Methods": df.columns[5:],
                        "Accuracy": [accuracy_score(df.cloud, df[col]) for col in df.columns[5:]]})

    # Creating feature - output dataset
    x_train, y_train = split_feature_output(df_evaluation)
    x_test, y_test = split_feature_output(df_evaluation)

    compute_accuracy_over_nb_estimators(x_train, x_test, y_train, y_test, show_plot=True)

    # Run random Forest
    res = random_forest_accuracy(res, x_train, y_train, x_test, y_test)
    # Run decision tree
    res = decision_tree_accuracy(res, x_train, y_train, x_test, y_test)
    # Run logistic regression model
    linear_logistic_regression(res, x_train, y_train, x_test, y_test)

    print("Results:\n", res)
    plot_accuracy_over_methods(res)
'''

