# -*- coding: utf-8 -*-
"""

    ppclassifier.py
    ~~~~~~~~~~~~~~

    This module trains, saves, loads and predicts locations for a single classifier.
    This is a wrapper for the machine learning section section of the system and
    the primary module that should be interacted with with dealing with classifiers.


    :author: Muzammil Abdul Rehman
    :copyright: Northeastern University © 2018.
    :license: Custom BSD, see LICENSE for more details.
    :email: passport@ccs.neu.edu

"""

from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import configs.system  # get configs.system.CLASSIFIER_FILES_DIR
import os
import json
import pickle
import copy
import pputils
from sklearn import tree
import traceback
from sklearn.externals.six import StringIO 
import pydot
###remove-me-later-muz###import pydotplus
# -*- coding: utf-8 -*-

# three types
# 1. initalize then load

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))


class GeoLocClassifier:
    """ The GeoLocClassifier object implements a wrapper around scikit-learn's decision tree
    and random forest classifiers for usage in the Passport system abstracting the machine learning
    details from the developer.
    """

    def __init__(self):
        """ Initialize the Classifier """
        #self.__dir_path
        self.classifiers_dir = os.path.join(PROJECT_ROOT,
                                            configs.system.CLASSIFIER_FILES_DIR_NAME)

        # name of the classifier
        self.classifier_name = ""

        # vector containing the training data. It's a list of lists
        self.__vec = None

        # vector containing the classsifier for each row in training data. It's a list
        self.__vec_classes = None

        # boolean containing whether a random forest should also be trained or not
        self.__forest_trained = False

        # sklearn tree classsifier
        self.__classifier_tree = None

        # sklearn forest classsifier
        self.__classifier_forest = None

    def train_classifier(self, training_data_list_org,
                                train_random_forest=False,
                                num_trees_forest=configs.system.NUM_TREE_IN_FOREST):
        """
        Train a single classifier

        :param training_data_list_org: A list of dictionary as follows (has realcountry field)
                            [{'db_ip_country': 'United States', 'asn': 0,
                             'maxmind_country': 'United States', 'ISPCountry': '',
                             'isp_region': '', 'isp': '', 'ipinfo_country': 'United States',
                             'DDECCountry': '', 'num_ipv4_prefix_in_org': 0,
                             'ip2location_country': 'United States', 'ASCountry': '',
                             'isp_city': '', 'num_as_in_org': 0, 'asn_registry': '',
                             'num_ipv4_ip_in_org': 0, 'as_name': '', 'realcountry': '',
                             'eurekapi_country': 'United States'}
        :param train_random_forest: Boolean about taining a random forest as well
        :param num_trees_forest: The number of trees in the random forest
        :return: Nothing
        """

        # deep copy since we are modifying the original data
        training_data_list = copy.deepcopy(training_data_list_org)
        self.__forest_trained = train_random_forest
        training_data = []
        training_classes = []
        for train_instance in training_data_list:
            # conver ip string to integer
            try:
                ip_int = pputils.ip_string_to_int(train_instance['ip'])
                train_instance['ip'] = ip_int 
            except:
                train_instance['ip'] = 0
                print "Couldn't add IP address to training data!"
            # add the real country to a new list
            training_classes.append(train_instance['realcountry'])
            del train_instance['realcountry']
            training_data.append(train_instance)

        # convert it to sklearn data
        self.__vec = DictVectorizer(sparse=False)
        vec_data = self.__vec.fit_transform(training_data)
        self.__vec_classes = LabelEncoder()
        classes_data = self.__vec_classes.fit_transform(training_classes)

        # Tain data
        self.__classifier_tree = DecisionTreeClassifier()
        self.__classifier_tree.fit(vec_data, classes_data)
        if self.__forest_trained:
            self.__classifier_forest = RandomForestClassifier(n_estimators=
                                                        num_trees_forest)
            self.__classifier_forest.fit(vec_data, classes_data)


    def predict(self, testing_instance_org):
        """

        :param testing_instance_org: {'db_ip_country': 'United States', 'asn': 0,
         'maxmind_country': 'United States', 'ISPCountry': '',
         'isp_region': '', 'isp': '', 'ipinfo_country': 'United States',
         'DDECCountry': '', 'num_ipv4_prefix_in_org': 0,
         'ip2location_country': 'United States', 'ASCountry': '',
         'isp_city': '', 'num_as_in_org': 0, 'asn_registry': '',
         'num_ipv4_ip_in_org': 0, 'as_name': '',
         'eurekapi_country': 'United States'}
        :return: a list as follows (2 or 4 elements)
                        ["tree", `country predicted by tree`, "forest", `country predicted by forest`]
        """

        testing_instance = copy.deepcopy(testing_instance_org)
        # conver ip string to integer
        try:
            ip_int = pputils.ip_string_to_int(testing_instance['ip'])
            testing_instance['ip'] = ip_int 
        except:
            testing_instance['ip'] = 0
        test_instance = self.__vec.transform(testing_instance)
        # predict
        tree_predicted = self.__classifier_tree.predict(test_instance)
        country_tree = self.__vec_classes.inverse_transform(tree_predicted)
        return_obj = ["tree", country_tree[0]]

        # don't addd foret information if no forest is there.
        if self.__forest_trained:
            forest_predicted = self.__classifier_forest.predict(test_instance)
            country_forest = self.__vec_classes.inverse_transform(
                                                            forest_predicted)
            return_obj.append("forest")
            return_obj.append(country_forest[0])
        # put in an array and return the data
        return return_obj


    def save_classifier_tree_graph(self, filename, depth = None):
        """
        Save the visualization of a tree

        :param filename: a string containing the filename not the path of save file
        :param depth: the depth of tree to be visualized
        :return: Nothing
        """
        # scikit 0.17
        # save dot
        save_file_name_dot = filename + ".dot"
        if depth is not None:            
            save_file_name_dot = filename +"_depth_" + str(depth) + ".dot"
        filepath_dot = os.path.join(PROJECT_ROOT,
                                     configs.system.CLASSIFIER_FILES_DIR_NAME,
                                     configs.system.SAVE_CLASSIFIERS_GRAPH_DIR,
                                     save_file_name_dot)
        # draw the tree
        tree.export_graphviz(self.__classifier_tree, out_file=filepath_dot, max_depth=depth,
                             feature_names=self.__vec.get_feature_names(), class_names=self.__vec_classes.classes_)
        # save pdf
        clf_dot_data = StringIO()
        tree.export_graphviz(self.__classifier_tree, out_file=clf_dot_data,max_depth=depth,
                             feature_names=self.__vec.get_feature_names(), class_names=self.__vec_classes.classes_)
        save_file_name = filename + ".pdf"
        if depth is not None:            
            save_file_name = filename +"_depth_" + str(depth) + ".pdf"
        filepath = os.path.join(PROJECT_ROOT,
                                     configs.system.CLASSIFIER_FILES_DIR_NAME,
                                     configs.system.SAVE_CLASSIFIERS_GRAPH_DIR,
                                     save_file_name)
        clf_dot_data_value = clf_dot_data.getvalue()
        #graph = pydotplus.graph_from_dot_data(clf_dot_data_value)
        #graph.write_pdf(filepath)
        graph = pydot.graph_from_dot_data(clf_dot_data_value)
        graph[0].write_pdf(filepath)

    def get_cls_copy(self):
        return copy.deepcopy(self.__classifier_tree)
    
    def get_vec_copy(self):
        return copy.deepcopy(self.__vec)


def save_classifier(geoloc_classifier, filename):
    """
    Save an instance of the GeoLocClassifier

    :param geoloc_classifier: An instance of <GeoLocClassifier>
    :param filename: A string containing the name of file to save the visualization of classifier (None otherwise).
    :return: A boolean depending on the success of saving the classifier
    """
    filepath = os.path.join(PROJECT_ROOT,
                                 configs.system.CLASSIFIER_FILES_DIR_NAME,
                                 filename)
    geoloc_classifier.classifier_name = filename.split(".")[0]
    try:
        with open(filepath, 'wb') as f:
            pickle.dump(geoloc_classifier, f)
        if configs.system.SAVE_CLASSIFIERS_GRAPH:
            geoloc_classifier.save_classifier_tree_graph(geoloc_classifier.classifier_name)
        return True
    except:
        return False

def load_classifier(filename):
    """
    Load an instance of the <GeoLocClassifier>

    :param filename: A string containing the name of classifier to be loaded
    :return: An instance of <GeoLocClassifier> or None
    """

    filepath = os.path.join(PROJECT_ROOT,
                                 configs.system.CLASSIFIER_FILES_DIR_NAME,
                                 filename)
    try:
        with open(filepath, 'rb') as f:
            geoloc_cls_obj = pickle.load(f)
    except:
        geoloc_cls_obj = None
    return geoloc_cls_obj


def load_all_classifiers():
    """
    Loads all the classifiers in the Passport system

    :return: A list of classifiers. [<GeoLocClassifier> 1, <GeoLocClassifier> 2, <GeoLocClassifier> 3 .....]
    """
    geoloc_classifiers = []
    folder = os.path.join(PROJECT_ROOT, configs.system.CLASSIFIER_FILES_DIR_NAME)
    for cls_file in os.listdir(folder):
        loaded_cls_obj = load_classifier(cls_file)
        if loaded_cls_obj is not None:
            geoloc_classifiers.append(loaded_cls_obj)
    return geoloc_classifiers



def delete_classifier(filename):
    """
    Deletes a specific file containing classifier

    :param filename: A string containing filename to be deleted
    :return: Nothing
    """
    filepath = os.path.join(PROJECT_ROOT,
                                 configs.system.CLASSIFIER_FILES_DIR_NAME,
                                 filename)
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except OSError:
        try:
            os.remove(filename)
        except:
            pass


def delete_all_classifiers():
    """A function to delete all the stored classifiers """

    folder = os.path.join(PROJECT_ROOT, configs.system.CLASSIFIER_FILES_DIR_NAME)
    for cls_file in os.listdir(folder):
        delete_classifier(cls_file)


###############################################################################
# basic testing section for the class
###############################################################################

def test():
    import urllib2
    import time

    def get_training_data():
        DATA_URL = "http://localhost:8080/georoute/get_all_train_dataset/"
        f = urllib2.urlopen(DATA_URL)
        response2 = f.read()
        trainingData = json.loads(response2)
        return trainingData

    start = time.time()
    training_data = get_training_data()
    end = time.time()
    print "Time to get the data: ", (end - start), "seconds"

    geoloc_cls_tree = GeoLocClassifier()
    print "Directory:", geoloc_cls_tree.classifiers_dir
    y = {'db_ip_country': 'United States', 'asn': 0,
         'maxmind_country': 'United States', 'ISPCountry': '',
         'isp_region': '', 'isp': '', 'ipinfo_country': 'United States',
         'DDECCountry': '', 'num_ipv4_prefix_in_org': 0,
         'ip2location_country': 'United States', 'ASCountry': '',
         'isp_city': '', 'num_as_in_org': 0, 'asn_registry': '',
         'num_ipv4_ip_in_org': 0, 'as_name': '', 'realcountry': '',
         'eurekapi_country': 'United States'}

    # tree only
    start = time.time()
    geoloc_cls_tree.train_classifier(training_data)
    end = time.time()
    print "Training time: ", (end - start), "seconds"

    start = time.time()
    res = geoloc_cls_tree.predict(y)
    end = time.time()
    print "Testing time: ", (end - start), "seconds"

    print "Result: ", res

    # tree and forest
    geoloc_cls_forest_tree = GeoLocClassifier()
    start = time.time()
    geoloc_cls_forest_tree.train_classifier(training_data, True)
    end = time.time()
    print "Training time with Random Forest: ", (end - start), "seconds"

    start = time.time()
    res = geoloc_cls_forest_tree.predict(y)
    end = time.time()
    print "Testing time with Random Forest: : ", (end - start), "seconds"

    print "Result: ", res

    # save the classifiers
    start = time.time()
    if save_classifier(geoloc_cls_tree, "tree.pkl"):
        end = time.time()
        print "Tree-only classifier saved"
        print "Total saving time: ", (end - start), "seconds"
    else:
        print "Failed to save tree-only classifier"
    start = time.time()
    if save_classifier(geoloc_cls_forest_tree, "tree_forest.pkl"):
        end = time.time()
        print "Dual classifier saved"
        print "Total saving time: ", (end - start), "seconds"
    else:
        print "Failed to save dual classifier"

    # load the classifiers
    start = time.time()
    classifiers_objects = load_all_classifiers()
    end = time.time()
    print "Total loading time: ", (end - start), "seconds"
    for cls_object in classifiers_objects:
        start = time.time()
        res = cls_object.predict(y)
        end = time.time()
        print "Predicting time : ", (end - start), "seconds"
        print "Result: ", res

    time.sleep(5)
    # delete the classifiers
    delete_all_classifiers()

if __name__ == "__main__":
    test()
