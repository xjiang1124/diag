#!/usr/bin/env python

import yaml
from collections import OrderedDict

#=========================================================
# To load yaml file in order
def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    class OrderedLoader(Loader):
        pass
    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)

def load_yaml(filename):
    with open(filename) as stream:
        try:
            #config_dict = yaml.load(stream)
            tsconfig = ordered_load(stream, yaml.SafeLoader)
        except yaml.YAMLError as exc:
            print exc
    return tsconfig

#=========================================================
# create output folder
def create_folder(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

