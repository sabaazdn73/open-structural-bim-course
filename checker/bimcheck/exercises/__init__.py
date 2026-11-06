"""Exercise registry. Each check is a function (args -> Result) registered with @exercise."""
REGISTRY = {}


def exercise(eid, title, inputs=("model.ifc",)):
    def wrap(fn):
        REGISTRY[eid] = {"id": eid, "title": title, "inputs": inputs, "fn": fn}
        return fn
    return wrap


from . import s1_project, s2_structure, s3_foundations_rebar, s4_types, s5_documentation, s6_sheets, s7_management  # noqa: E402,F401
