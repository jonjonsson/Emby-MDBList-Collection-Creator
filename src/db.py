import os
import configparser


class Db:
    """
    Simple db using a configuration file to store and retrieve values.
    """

    def __init__(self, temp_dir="temp", config_file_name="db.cfg"):
        self.temp_dir = temp_dir
        self.config_file = os.path.join(self.temp_dir, config_file_name)
        self.config, _ = self.ensure_db_config()

    def ensure_db_config(self):
        """
        Ensures that the db.cfg file and temp directory exist.

        Returns:
            configparser.ConfigParser: The configuration parser object.
        """
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        config = configparser.ConfigParser()

        if os.path.exists(self.config_file):
            config.read(self.config_file)

        return config, self.config_file

    def get_config_for_section(self, section, param_name):
        """
        Args:
            section (str): The name of the section.
            param_name (str): The name of the parameter to retrieve.

        Returns:
            str: The value of the specified parameter for the section, or None if not found.
        """
        section = str(section)
        if section in self.config.sections():
            return self.config.get(section, param_name, fallback=None)
        return None

    def set_config_for_section(self, section, param_name, param_value):
        """
        Sets the configuration for a collection.

        Args:
            section (str): The name of the section.
            param_name (str): The name of the parameter to set.
            param_value (str): The value of the parameter to set.
        """
        section = str(section)
        if section not in self.config.sections():
            self.config.add_section(section)
        self.config.set(section, param_name, param_value)

        with open(self.config_file, "w") as configfile:
            self.config.write(configfile)
