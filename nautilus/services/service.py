# external imports
import os
import requests
import tornado.ioloop
import tornado.web
# local imports
import nautilus
from nautilus.network.amqp.consumers.actions import ActionHandler
from nautilus.api.endpoints import static_dir as api_endpoint_static
import nautilus.network.registry as registry
from nautilus.config import Config
from nautilus.api.endpoints import (
    GraphiQLRequestHandler,
    GraphQLRequestHandler
)

class ServiceMetaClass(type):
    def __init__(self, name, bases, attributes):
        # create the super class
        super().__init__(name, bases, attributes)
        # save the name to the class record
        self.name = name


class Service(metaclass=ServiceMetaClass):
    """
        This is the base class for all services that are part of a nautilus
        cloud. This class provides basic functionalities such as registration,
        responding to actions, and predictable api endpoints.

        Args:

            action_handler (optional, function): The callback function fired when
                an action is recieved. If None, the service does not connect to the
                action queue.

            config (optional, class): A python class to use for configuring the
                service.

            name (string): The name of the service. This will be used to
                register the service with the registry as act as the designator
                for a ServiceObjectType.

            schema (optional, graphql.core.type.GraphQLSchema): The GraphQL schema
                which acts as a basis for the external API. If None, no endpoints are
                added to the service.

        Example:

            .. code-block:: python

                import nautilus
                from nautilus.api import create_model_schema
                from nautilus.network import crud_handler
                import nautilus.models as models

                class Model(models.BaseModel):
                    name = models.fields.CharField()

                class MyService(nautilus.Service):
                    name = 'My Awesome Service'
                    schema = create_model_schema(Model)
                    action_handler = crud_handler(Model)
    """

    action_handler = None
    config = None
    name = None
    schema = None

    def __init__(
            self,
            name=None,
            schema=None,
            action_handler=None,
            config=None,
            auth=True,
    ):

        self.name = self.name or name or type(self).name
        self.__name__ = name
        self.action_handler = action_handler or self.action_handler
        self.keep_alive = None
        self._action_handler_loop = None
        self.schema = schema or self.schema

        # wrap the given configuration in the nautilus wrapper
        self.config = Config(self.config, config)

        # base the service on a tornado app
        self.app = self.tornado_app

        # setup various functionalities
        self.init_action_handler(self.action_handler)


    @property
    def tornado_app(self):
        # create a tornado web application
        app = tornado.web.Application(
            self.request_handlers,
            debug=self.config.get('debug',False),
            cookie_secret=self.config.get('secret_key', 'default_secret')
        )
        # attach the ioloop to the application
        app.ioloop = tornado.ioloop.IOLoop.instance()
        # return the app instance
        return app


    def init_action_handler(self, action_handler):
        # if the service was provided an action handler
        if action_handler:
            # create a wrapper for it
            self._action_handler_loop = ActionHandler(callback=action_handler)
            # add it to the ioloop
            self.app.ioloop.add_callback(self._action_handler_loop.run)


    def init_keep_alive(self):
        # create the period callback
        self.keep_alive = registry.keep_alive(self)


    def run(self, host="localhost", port=8000, **kwargs):
        """
            This function starts the service's network intefaces.

            Args:
                port (int): The port for the http server.
        """
        print("Running service on http://localhost:%i. " % port + \
                                            "Press Ctrl+C to terminate.")
        # create the keep alive timer
        self.init_keep_alive()

        # start the keep alive timer
        self.keep_alive.start()
        # assign the port to the app instance
        self.app.listen(port, address=host)

        # start the ioloop
        try:
            self.app.ioloop.start()
        # if the user interrupts the server
        except KeyboardInterrupt as err:
            # stop the service and clean up
            self.stop()
            # bubble the exception up to someone who cares
            raise err
        except Exception as err:
            # stop the service and clean up
            self.stop()
            # bubble the exception up to someone who cares
            raise err


    def stop(self):
        """
            This function stops the service's various network interfaces.
        """
        # if there is a keep alive timer
        if self.keep_alive:
            # stop the keep_alive timer
            self.keep_alive.stop()
            # remove the service entry from the registry
            registry.deregister_service(self)

        # stop the ioloop
        self.app.ioloop.stop()

        # if there is an action consumer registered with this service
        if self._action_handler_loop:
            # stop the action consumer
            self._action_handler_loop.stop()


    @property
    def request_handlers(self):
        return [
            (r"/", GraphQLRequestHandler, dict(schema=self.schema)),
            (r"/graphiql/?", GraphiQLRequestHandler),
            (r"/graphiql/static/(.*)", tornado.web.StaticFileHandler,
                                            dict(path=api_endpoint_static)),
        ]


    def add_http_endpoint(self, url, request_handler, config=None, host=".*$"):
        """
            This method provides a programatic way of added invidual routes
            to the http server.

            Args:
                url (str): the url to be handled by the request_handler
                request_handler (tornado.web.RequestHandler): The request handler
                config (dict): A configuration dictionary to pass to the handler
        """
        self.app.add_handlers(host, [(url, request_handler, config)])


    def route(self, route, config=None):
        """
            This method provides a decorator for adding endpoints to the
            http server.

            Args:
                route (str): The url to be handled by the RequestHandled
                config (dict): Configuration for the request handler

            Example:

                .. code-block:: python

                    import nautilus
                    from nauilus.network.http import RequestHandler

                    class MyService(nautilus.Service):
                        # ...

                    @MyService.route('/')
                    class HelloWorld(RequestHandler):
                        def get(self):
                            return self.finish('hello world')
        """
        def decorator(cls, **kwds):
            # add the endpoint at the given route
            self.add_http_endpoint(url = route, request_handler=cls, config=kwds)
            # return the class undecorated
            return cls

        # return the decorator
        return decorator


    # def setup_auth(self):
    #     # if we are supposed to enable authentication for the service
    #     if self.auth:
    #         from nautilus.auth import init_service
    #         init_service(self)
