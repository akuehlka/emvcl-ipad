# -*- coding: utf-8 -*-

import os
import itertools
import numpy as np
from glob import glob
from antispoofing.mcnns.datasets.dataset import Dataset
from antispoofing.mcnns.utils import *


class LivDet_ND_WW(Dataset):
    def __init__(self, dataset_path, ground_truth_path='', permutation_path='', iris_location='',
                 output_path='./working', file_types=('.png', '.bmp', '.jpg', '.tiff'),
                 operation='crop', max_axis=320,
                 ):

        super(LivDet_ND_WW, self).__init__(dataset_path, output_path, iris_location, file_types, operation, max_axis)

        self.ground_truth_path = ground_truth_path
        self.LIV_DET_TRAIN = os.path.join(self.ground_truth_path, 'train.csv')
        self.LIV_DET_TEST = os.path.join(self.ground_truth_path, 'test.csv')
        self.LIV_DET_UNKNOWN_TEST = os.path.join(self.ground_truth_path, 'unknown_test.csv')
        self.verbose = True

    def _build_meta(self, inpath, filetypes):

        img_idx = 0

        all_fnames = []
        all_labels = []
        all_idxs = []
        train_idxs = []
        test_idxs = []
        unknown_test_idxs = []

        hash_img_id = {}

        liv_det_train_data, liv_det_train_hash = read_csv_file(self.LIV_DET_TRAIN, sequenceid_col=0, delimiter=',',
                                                               remove_header=False)
        liv_det_test_data, liv_det_test_hash = read_csv_file(self.LIV_DET_TEST, sequenceid_col=0, delimiter=',',
                                                             remove_header=False)
        liv_det_unknown_test_data, liv_det_unknown_test_hash = read_csv_file(self.LIV_DET_UNKNOWN_TEST,
                                                                             sequenceid_col=0, delimiter=',',
                                                                             remove_header=False)

        folders = [self.list_dirs(inpath, filetypes)]
        folders = sorted(list(itertools.chain.from_iterable(folders)))

        for i, folder in enumerate(folders):
            progressbar('-- folders', i, len(folders), new_line=True)

            fnames = [glob(os.path.join(inpath, folder, '*' + filetype)) for filetype in filetypes]
            fnames = sorted(list(itertools.chain.from_iterable(fnames)))

            for j, fname in enumerate(fnames):

                rel_path = os.path.relpath(fname, inpath)
                img_id, ext = os.path.splitext(os.path.basename(rel_path))

                if img_id in liv_det_train_hash:

                    if not (img_id in hash_img_id):
                        hash_img_id[img_id] = img_idx
                        train_idxs += [img_idx]
                        all_labels += [int(liv_det_train_data[liv_det_train_hash[img_id]][1])]
                        all_fnames += [fname]
                        all_idxs += [img_idx]
                        img_idx += 1

                elif img_id in liv_det_test_hash:

                    if not (img_id in hash_img_id):
                        hash_img_id[img_id] = img_idx
                        test_idxs += [img_idx]
                        all_labels += [int(liv_det_test_data[liv_det_test_hash[img_id]][1])]
                        all_fnames += [fname]
                        all_idxs += [img_idx]
                        img_idx += 1

                elif img_id in liv_det_unknown_test_hash:

                    if not (img_id in hash_img_id):
                        hash_img_id[img_id] = img_idx
                        unknown_test_idxs += [img_idx]
                        all_labels += [int(liv_det_unknown_test_data[liv_det_unknown_test_hash[img_id]][1])]
                        all_fnames += [fname]
                        all_idxs += [img_idx]
                        img_idx += 1

                else:
                    pass

        all_fnames = np.array(all_fnames)
        all_labels = np.array(all_labels)
        all_idxs = np.array(all_idxs)
        train_idxs = np.array(train_idxs)
        test_idxs = np.array(test_idxs)
        unknown_test_idxs = np.array(unknown_test_idxs)

        all_pos_idxs = np.where(all_labels[all_idxs] == self.POS_LABEL)[0]
        all_neg_idxs = np.where(all_labels[all_idxs] == self.NEG_LABEL)[0]

        r_dict = {'all_fnames': all_fnames,
                  'all_labels': all_labels,
                  'all_idxs': all_idxs,
                  'all_pos_idxs': all_pos_idxs,
                  'all_neg_idxs': all_neg_idxs,
                  'train_idxs': train_idxs,
                  'test_idxs': {'test': test_idxs,
                                'unknown_test': unknown_test_idxs,
                                },
                  'hash_img_id': hash_img_id,
                  }

        if self.verbose:
            self.info(r_dict)

        return r_dict

    def protocol_eval(self, fold=0, n_fold=5, train_size=0.5):

        # -- loading the training data and its labels
        all_fnames = self.meta_info['all_fnames']
        all_labels = self.meta_info['all_labels']
        train_idxs = self.meta_info['train_idxs']
        test_idxs = self.meta_info['test_idxs']

        all_data = self.get_imgs(all_fnames)

        train_set = {'data': all_data[train_idxs],
                     'labels': all_labels[train_idxs],
                     'idxs': train_idxs}

        test_set = {}
        for test_id in test_idxs:
            if test_idxs[test_id].size:
                test_set[test_id] = {'data': all_data[test_idxs[test_id]],
                                     'labels': all_labels[test_idxs[test_id]],
                                     'idxs': test_idxs[test_id],
                                     }

        return {'train_set': train_set, 'test_set': test_set}
