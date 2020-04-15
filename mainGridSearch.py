# Classifiers
from classifiers import svm, rf, knn, nnn, nb

# Classifiers evaluation methods
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold

# Utils
from sklearn.utils.multiclass import unique_labels
import numpy as np
import pandas as pd
import time
import initContext as context
from config import logger

from asd_data import load_by_chunks
context.loadModules()
log = logger.getLogger(__file__)


def run_optimization(dataset='euclidian_px_all', n_labels=111, filtro=0.0):
    log.info("Running Grid Search for %s dataset", dataset)

    dimensionality_reductions = [
        'None',
        'PCA',
        'mRMRProxy',
        'FCBFProxy',
        'CFSProxy',
        'RFSProxy',
        'ReliefF'
    ]

    classifiers = {
        'randomforestclassifier': rf,
        # 'svc': svm,
        # 'kneighborsclassifier': knn,
        # 'mlpclassifier': nnn
    }

    labels = pd.read_csv(filepath_or_buffer='./data/reduction_files/labels_{0}.csv'.format(dataset))
    labels = np.array(labels).reshape(n_labels, )  # Convert a pandas dataframe to a 1D numpy array

    rf_is_done = False  # variavel de controle para rodar o random forests somente uma vez
    for classifier in classifiers.keys():
        for dimensionality_reduction in dimensionality_reductions:
            if classifier is not 'randomforestclassifier':
                reduction = dimensionality_reduction
                if filtro != 0.0:
                    path = './data/reduction_files/{0}_{1}_filtro_{2}.csv'.format(reduction, dataset, filtro)
                else:
                    path = './data/reduction_files/{0}_{1}.csv'.format(reduction, dataset)
            else:
                if rf_is_done:
                    break

                if filtro != 0.0:
                    path = './data/reduction_files/None_{0}_filtro {1}.csv'.format(dataset, filtro)
                else:
                    path = './data/reduction_files/None_{0}.csv'.format(dataset)

                rf_is_done = True
                reduction = None

            log.info('Reading files for {0} dataset'.format(dataset))
            log.info('Dataset file: %s', str(path))

            samples = pd.read_csv(filepath_or_buffer=path)
            samples = samples.to_numpy()

            instances, features = samples.shape
            n_classes = len(unique_labels(labels))
            n_features_to_keep = int(np.sqrt(features))

            log.info('Data has {0} classes, {1} instances and {2} features'.format(n_classes, instances, features))
            log.info("X.shape %s, y.shape %s", str(samples.shape), str(labels.shape))

            scoring = {
                'accuracy': 'accuracy',
                'precision_macro': 'precision_macro',
                'recall_macro': 'recall_macro',
                'f1_macro': 'f1_macro'}

            estimators, param_grid, classifier_name = classifiers[classifier].make_grid_optimization_pipes(
                n_features_to_keep)
            cv = StratifiedKFold(n_splits=4)
            for estimator in estimators:
                try:
                    log.info("Training Models for %s and %s", classifier_name, reduction)

                    grd = GridSearchCV(
                        estimator=estimator,
                        param_grid=param_grid,
                        scoring=scoring,
                        cv=cv,
                        refit='accuracy',
                        return_train_score=False,
                        n_jobs=-1  # -1 means all CPUs
                        # For n_jobs below -1, (n_cpus + 1 + n_jobs) are used.
                    )
                    grid_results = grd.fit(samples, labels)

                    log.info("Training complete")

                except ValueError as e:
                    log.exception("Exception during pipeline execution", extra=e)
                    grid_results = None
                except KeyError as ke:
                    log.exception("Exception during pipeline execution", extra=ke)
                    grid_results = None

                if grid_results is not None:
                    log.info("Best result presented accuracy %.2f%% for %s and %s",
                             grid_results.best_score_ * 100, classifier_name, reduction)
                    log.info("Best parameters found: {0}".format(grid_results.best_params_))
                    log.info("Best parameters were found on index: {0}".format(grid_results.best_index_))

                    log.info("Saving results!")
                    df_results = pd.DataFrame(grid_results.cv_results_)
                    df_results.drop('params', axis=1)
                    path_results = './output/GridSearch/results_{0}_{1}_{2}.csv'.format(dataset,
                                                                                        classifier_name,
                                                                                        reduction)
                    df_results.to_csv(path_results, index_label='id')


if __name__ == '__main__':
    start_time = time.time()
    run_optimization(n_labels=94)
    # run_optimization(dataset='wine', n_labels=178)
    # run_optimization(dataset='glass', n_labels=214)
    log.info("--- Total execution time: %s minutes ---" % ((time.time() - start_time) / 60))
