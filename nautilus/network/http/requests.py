from tornado.web import RequestHandler as TornadoRequestHandler

class RequestHandler(TornadoRequestHandler):
    """
        The base class for nautilus http request handlers.

        Example:

            import nautilus
            from nautilus.network.http import RequestHandler

            service = nautilus.Service(...)

            @service.route('/')
            class RequestHandler:
                def get(self):
                    self.finish('hello')
    """