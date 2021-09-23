import copy
import logging

import yaml

logger = logging.getLogger("bend_tester")

DEFAULT_CFG = {
    "main": {
        "real_size": [90, 68],  # 16:9
        "aml": 20,
        "threshold": 1.8,  # mm
        "interval": 50,  # ms
        "scale_abs": {"alpha": 2, "beta": 50,},
        "gauss_blur": {"ksize": [5, 5], "sigmaX": 1.5,},
        "canny": {"threshold1": 100, "threshold2": 50,},
        "dilate": {"kernel": [5, 5], "iterations": 3,},
        "erode": {"kernel": [3, 3], "iterations": 3,},
        "hough_line_p": {
            "rho": 1,
            "theta": 8.7e-4,
            "threshold": 15,
            "minLineLength": 40,
            "maxLineGap": 10,
        },
        "style": {"line_color": [255, 255, 0]},
    },
    "job": {
        "output_dir": "./run",
        "box_id": "XXXXXX",
        "operator": []
    },
    "run": {},
}


class Config(object):
    """Helper class to handle job configs"""

    def __init__(self, config: dict) -> None:
        # define supported sections to avoid lint error
        self.main = Config_Section({})
        self.job = Config_Section({})
        self.run = Config_Section({})
        # set default
        self.update(DEFAULT_CFG)
        # initialize config
        for key, value in config.items():
            if type(value) is dict:
                getattr(self, key).update(value)
            elif value is None:
                pass
            else:
                logger.critical(
                    f"Expect section {key} must has dict type value or None, please check the input."
                )
                raise ValueError

    def clone(self):
        return copy.deepcopy(self)

    def get_config_dict(self) -> dict:
        """ Returns config in dict format """
        out_dict = {}
        out_dict["config"] = self.config.get_config_dict()
        out_dict["job"] = self.job.get_config_dict()
        out_dict["input"] = self.input.get_config_dict()
        out_dict["train"] = self.train.get_config_dict()
        out_dict["tune"] = self.tune.get_config_dict()
        out_dict["apply"] = self.apply.get_config_dict()
        out_dict["para_scan"] = self.para_scan.get_config_dict()
        out_dict["run"] = self.run.get_config_dict()
        return out_dict

    def update(self, config: dict) -> None:
        """Updates configs with given config dict, overwrite if exists

        Args:
            config (dict): two level dictionary of configs
        """
        for key, value in config.items():
            if type(value) is dict:
                if key in self.__dict__.keys():
                    getattr(self, key).update(value)
                else:
                    setattr(self, key, Config_Section(value))
            elif value is None:
                pass
            else:
                logger.critical(
                    f"Expect section {key} has dict type value or None, please check the input."
                )
                raise ValueError

    def print(self) -> None:
        """Shows all configs
        """
        print("")
        print("Config details " + ">" * 80)
        for key, value in self.__dict__.items():
            print(f"[{key}]")
            value.print()
        print("Config ends " + "<" * 83)
        print("")


class Config_Section(object):
    """Helper class to handle job configs in a section"""

    def __init__(self, section_config_dict: dict) -> None:
        for key, value in section_config_dict.items():
            if type(value) is dict:
                setattr(self, key, Config_Section(value))
            else:
                setattr(self, key, value)

    def __deepcopy__(self, memo):
        clone_obj = Config_Section(self.get_config_dict())
        return clone_obj

    def __getattr__(self, item):
        """Called when an attribute lookup has not found the attribute in the usual places"""
        return None

    def clone(self):
        return copy.deepcopy(self)

    def get_config_dict(self) -> dict:
        """ Returns config in dict format """
        config_dict = dict()
        for key, value in self.__dict__.items():
            if key != "_config_dict":
                if isinstance(value, Config_Section):
                    config_dict[key] = value.get_config_dict()
                else:
                    config_dict[key] = value
        return config_dict

    def update(self, cfg_dict: dict) -> None:
        """Updates the section config dict with new dict, overwrite if exists

        Args:
            cfg_dict (dict): new section config dict for update
        """
        for key, value in cfg_dict.items():
            if type(value) is dict:
                if (
                    key in self.__dict__.keys()
                    and key != "_config_dict"
                    and isinstance(getattr(self, key), Config_Section)
                ):
                    getattr(self, key).update(value)
                else:
                    setattr(self, key, Config_Section(value))
            else:
                setattr(self, key, value)

    def print(self, tabs=0) -> None:
        """Shows all section configs
        """
        for key, value in self.__dict__.items():
            if key != "_config_dict":
                if isinstance(value, Config_Section):
                    print(f"{' '*4*tabs}    {key} :")
                    value.print(tabs=tabs + 1)
                elif isinstance(value, list):
                    print(f"{' '*4*tabs}    {key} :")
                    for ele in value:
                        print(f"{' '*4*tabs}        - {ele}")
                else:
                    print(f"{' '*4*tabs}    {key} : {value}")


def load_yaml_dict(yaml_path) -> dict:
    try:
        yaml_file = open(yaml_path, "r")
        return yaml.load(yaml_file, Loader=yaml.FullLoader)
    except:
        logger.critical(
            f"Can't read yaml config: {yaml_path}, please check whether input yaml config exists and the syntax is correct"
        )
        raise IOError
