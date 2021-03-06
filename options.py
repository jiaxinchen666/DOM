import numpy as np
import os
import glob
import torch
import argparse


def parse_args(script):
    parser = argparse.ArgumentParser(description='few-shot script %s' % (script))
    parser.add_argument('--dataset', default=['cars', 'flowers', 'cub', 'fungi'])
    parser.add_argument('--testset', default='flowers', help='cub/cars/fruits/vegetable/plantae/fungi/flowers')
    parser.add_argument('--model', default='ResNet10')
    parser.add_argument('--method', default='protonet',
                        help='protonet/relationnet/gnnnet/matchingnet')
    parser.add_argument('--train_n_way', default=5, type=int, help='class num to classify for training')
    parser.add_argument('--test_n_way', default=5, type=int, help='class num to classify for testing (validation) ')
    parser.add_argument('--n_shot', default=1, type=int, help='number of labeled data in each class, same as n_support')
    parser.add_argument('--n_query', default=5, type=int, help="number of queries")
    parser.add_argument('--train_aug', default='True',type=str, help='perform data augmentation or not during training ')
    parser.add_argument('--save_dir', default='./output', type=str, help='')
    parser.add_argument('--data_dir', default='./filelists', type=str, help='')
    parser.add_argument('--domain_specific',default='True',type=str,help='only for ours')
    parser.add_argument('--mode',default='train_and_test',type=str,help='onlytest/onlytrain/train_and_test')
    parser.add_argument('--lr',default=0.1,type=float,help='for domain adaptation')
    parser.add_argument('--stop_epoch', default=1, type=int, help='Stopping epoch')

    if script == 'train':
        parser.add_argument('--num_classes', default=200, type=int,
                            help='total number of classes in softmax, only used in baseline')
        parser.add_argument('--save_freq', default=50, type=int, help='Save frequency')
        parser.add_argument('--start_epoch', default=0, type=int, help='Starting epoch')
        parser.add_argument('--resume', default='', type=str,
                            help='continue from previous trained model with largest epoch')
        parser.add_argument('--resume_epoch', default=-1, type=int, help='')
        parser.add_argument('--warmup', default='baseline', type=str,
                            help='continue from baseline, neglected if resume is true')
    elif script == 'test':
        parser.add_argument('--split', default='novel', help='base/val/novel')
        parser.add_argument('--save_epoch', default=-1, type=int,
                            help='save feature from the model trained in x epoch, use the best model if x is -1')
    else:
        raise ValueError('Unknown script')

    return parser.parse_args()

def get_assigned_file(checkpoint_dir, num):
    assign_file = os.path.join(checkpoint_dir, '{:d}.tar'.format(num))
    return assign_file

def get_resume_file(checkpoint_dir, resume_epoch=-1):
    filelist = glob.glob(os.path.join(checkpoint_dir, '*.tar'))
    if len(filelist) == 0:
        return None

    filelist = [x for x in filelist if os.path.basename(x) != 'best_model.tar']
    epochs = np.array([int(os.path.splitext(os.path.basename(x))[0]) for x in filelist])
    max_epoch = np.max(epochs)
    epoch = max_epoch if resume_epoch == -1 else resume_epoch
    resume_file = os.path.join(checkpoint_dir, '{:d}.tar'.format(epoch))
    return resume_file


def get_best_file(checkpoint_dir):
    best_file = os.path.join(checkpoint_dir, 'best_model.tar')
    if os.path.isfile(best_file):
        return best_file
    else:
        return get_resume_file(checkpoint_dir)


def load_warmup_state(filename, method):
    print('  load pre-trained model file: {}'.format(filename))
    warmup_resume_file = get_resume_file(filename)
    tmp = torch.load(warmup_resume_file)
    if tmp is not None:
        state = tmp['state']
        state_keys = list(state.keys())
        for i, key in enumerate(state_keys):
            '''if "feature." in key and '.7.' not in key:
                newkey = key.replace("feature.", "")
                state[newkey] = state.pop(key)
            elif "feature." in key and '.7.' in key:
                newkey = key.replace("feature.trunk.7", "trunk1.0")
                state[newkey] = state.pop(key)'''
            if 'relationnet' in method and "feature." in key:
                newkey = key.replace("feature.","")
                state[newkey] = state.pop(key)
            elif method == 'gnnnet' and 'feature.' in key:
                newkey = key.replace("feature.","")
                state[newkey] = state.pop(key)
            elif method == 'protonet' and 'feature.' in key:
                newkey = key.replace("feature.","")
                state[newkey] = state.pop(key)
            elif method == 'matchingnet' and 'feature.' in key and '.7.' not in key:
                newkey = key.replace("feature.","")
                state[newkey] = state.pop(key)
            else:
                state.pop(key)
    else:
        raise ValueError(' No pre-trained encoder file found!')
    return state
