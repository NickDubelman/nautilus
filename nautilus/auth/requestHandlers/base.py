# local imports
from nautilus.network.http import RequestHandler
from nautilus.network import query_service
from nautilus.conventions.services import auth_service_name
from nautilus.network.registry import service_location_by_name

class AuthRequestHandler(RequestHandler):
    # NEED SOME FORM OF:
    # app.config['REMEMBER_COOKIE_DOMAIN'] = '.syncatech.com'

    def get_current_user(self):
        """
            This function retrieves the user identifier from the request
        """
        # get the id of the user form the token
        return self.get_secure_cookie(self._token_name)


    def get_login_url(self):
        """
            This method returns the url that handles logging-in.
        """
        # return the location of the service with the conventional auth name
        return "http://" + service_location_by_name(auth_service_name())


    def login_user(self, user):
        """
            This function logs the given user in on the request request.
        """
        self.set_secure_cookie(self._token_name, self._token_contents(user))


    def logout_user(self):
        """
            This method logs the current user out by clearing the cookie.
        """
        self.clear_cookie(self._token_name)


    @property
    def _token_name(self):
        """
            The name of the authentication cookie
        """
        return "nautilus_jwt"


    def _token_contents(self, user):
        """
            This method provides the jwt contents for the given user.
        """
        return user.id