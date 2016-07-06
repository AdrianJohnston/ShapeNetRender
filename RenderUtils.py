
def type_check(value, type_class):

    for k,v in type_class.__dict__.iteritems():
        if k is not '__module__' or k is not '__doc__':
            if v == value:
                return True

    return False
