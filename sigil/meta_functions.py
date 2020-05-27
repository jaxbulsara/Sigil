PROPERTY_GETTER = """
def {name}(self):
    return self._{name}.value
"""

PROPERTY_SETTER = """
def {name}(self, value):
    self._{name}.value = value
"""

ID_GETTER = """
def {name}(self):
    return self._{name}
"""

ID_SETTER = """
def {name}(self, value):
    if type(value) == int:
        self._{name} = value
    else:
        raise TypeError(f"id must be of type int, not {{type(value)}}")
"""
