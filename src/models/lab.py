# returns the lab if exists
def find_lab(labs, name):
    for lab in labs:
        if lab.name == name:
            return lab
        return None
    
def lab_exists(labs, name):
    return find_lab(labs, name) is not None