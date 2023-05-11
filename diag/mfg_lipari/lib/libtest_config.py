import yaml
from collections import OrderedDict
from pprint import pprint
import itertools

def parse_config(filename):
  with open(filename, "r") as cfg_fd:
    try:
      yaml_config = ordered_load(cfg_fd, yaml.SafeLoader)
    except yaml.YAMLError as exc:
      print(exc)
      return None
  
  return yaml_config

def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):

  class OrderedLoader(Loader):
    pass

  def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    return object_pairs_hook(loader.construct_pairs(node))

  OrderedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                                construct_mapping)
  return yaml.load(stream, OrderedLoader)


### add to each table, or just particular ones
def add_config_field(config_table,
                     field,
                     val,
                     exp_stage="ALL",
                     exp_platform="ALL"):
  for stage in list(STAGES):
    if exp_stage not in ("ALL", "DEFAULT") and stage != exp_stage:
      continue
    for platform in list(PLATFORMS):
      if exp_platform not in ("ALL", "DEFAULT") and platform != exp_platform:
        continue
      config_table[stage][platform][field] = val
      # print("Set [{}][{}][{}] to {}".format(stage, platform, field, val))


### traverse yaml config:
###   for a field-value pair, add to config table
###   if field is one of the keywords, squash the field and add its value to the parent fields
def traverse_dict(dictionary,
                  final_config_table,
                  parent_field=None,
                  stage="ALL",
                  platform="ALL"):
  for field, val in dictionary.items():
    # print((stage, platform, parent_field, field, val))
    if field in STAGES + ["DEFAULT", "ALL"]:
      stage = field
    elif field in PLATFORMS + ["DEFAULT", "ALL"]:
      platform = field
    else:
      parent_field = field
    if isinstance(val, str):
      add_config_field(final_config_table, parent_field, val, stage, platform)
    else:
      traverse_dict(val, final_config_table, parent_field, stage, platform)
