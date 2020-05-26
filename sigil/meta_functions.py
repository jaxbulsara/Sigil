PROPERTY_GETTER = """
def {name}(self):
    return self._{name}.value
"""

PROPERTY_SETTER = """
def {name}(self, value):
    self._{name}.value = value
"""
