"""
    This file is responsible for centralizing the service conventions used in nautilus.
"""

# local imports
from .models import get_model_string

def model_service_name(model):
    ''' the name of a service that manages a model '''
    return get_model_string(model)


def connection_service_name(*args):
    ''' the name of a service that manages the connection between services '''

    # the list of services to connect
    services = []

    # for each service to connect
    for service in args:
        # if the service was passed as a string
        if isinstance(service, str):
            # add it to the list
            services.append(service)
        # otherwise the serivice was not a string
        else:
            services.append(get_model_string(model))

    # combine the two names into the connection name
    return "{}_connection".format('_'.join(sorted(services)))
