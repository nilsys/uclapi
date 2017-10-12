import datetime
import re
import redis

from dashboard.models import App, TemporaryToken
from dashboard.tasks import keen_add_event_task as keen_add_event

from oauth.models import OAuthToken
from oauth.scoping import Scopes

from roombookings.helpers import JsonResponse as JsonResponse

from .settings import REDIS_UCLAPI_HOST


# Gets a variable from GET or POST not caring which is which
def get_var(request, var_name):
    if var_name in request.GET:
        return request.GET[var_name]
    elif var_name in request.POST:
        return request.POST[var_name]
    else:
        return None


class UclApiIncorrectDecoratorUsageException(Exception):
    pass


class UclApiIncorrectTokenTypeException(Exception):
    pass


def how_many_seconds_until_midnight():
    """Returns the number of seconds until midnight."""
    tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
    midnight = datetime.datetime(
        year=tomorrow.year, month=tomorrow.month,
        day=tomorrow.day, hour=0, minute=0, second=0
    )
    return (midnight - datetime.datetime.now()).seconds


def log_api_call(request, token, token_type):
    service = request.path.split("/")[1]
    method = request.path.split("/")[2]

    headers = request.META
    version_headers = {}
    regex = re.compile("^HTTP_UCLAPI_.*_VERSION$")
    for header in headers:
        if regex.match(header):
            version_headers[header] = headers[header]

    queryparams = dict(request.GET)

    if token_type == "oauth":
        parameters = {
            "userid": token.user.id,
            "email": token.user.email,
            "name": token.user.given_name,
            "service": service,
            "method": method,
            "version-headers": version_headers,
            "queryparams": queryparams,
            "temp_token": False,
            "token_type": token_type
        }
    elif token_type == "general-temp":
        parameters = {
            "service": service,
            "method": method,
            "version-headers": version_headers,
            "queryparams": queryparams,
            "temp_token": True,
            "token_type": token_type
        }
    elif token_type == "general":
        parameters = {
            "userid": token.user.id,
            "email": token.user.email,
            "name": token.user.given_name,
            "service": service,
            "method": method,
            "version-headers": version_headers,
            "queryparams": queryparams,
            "temp_token": False,
            "token_type": token_type
        }

    keen_add_event.delay("apicall", parameters)


def throttle_api_call(token, token_type):
    if token_type == 'general':
        cache_key = token.user.email
        limit = 10000
    elif token_type == 'general-temp':
        cache_key = token.api_token
        limit = 100
    elif token_type == 'oauth':
        cache_key = token.user.email
        limit = 10000
    else:
        raise UclApiIncorrectTokenTypeException

    r = redis.StrictRedis(host=REDIS_UCLAPI_HOST)
    count = r.get(cache_key)

    secs = how_many_seconds_until_midnight()
    if count is None:
        r.set(cache_key, 1, secs)
        return (False, limit, limit - 1, secs)
    else:
        if count > limit:
            return (True, limit, limit - count, secs)
        else:
            r.incr(cache_key)
            return (False, limit, limit - count, secs)


def uclapi_protected_endpoint(personal_data=False, required_scopes=None):
    def token_scope_check(view_func):
        def wrapped(request, *args, **kwargs):
            # A small sanity check
            # You cannot apply a personal data scope if you are not using
            # a personal data flag
            if personal_data is False:
                if required_scopes is not None:
                    raise UclApiIncorrectDecoratorUsageException

            # In any case, a token should be provided
            token_code = get_var(request, 'token')
            if token_code is None:
                response = JsonResponse({
                    "ok": False,
                    "error": "No token provided."
                })
                response.status

            if token_code.startswith('uclapi-user-'):
                # The token is an OAuth token, so apply OAuth logic
                client_secret = get_var(request, 'client_secret')
                if client_secret is None:
                    response = JsonResponse({
                        "ok": False,
                        "error": "No Client Secret provided."
                    })
                    response.status_code = 400
                    return response

                try:
                    token = OAuthToken.objects.get(token=token_code)
                except OAuthToken.DoesNotExist:
                    response = JsonResponse({
                        "ok": False,
                        "error": "Token does not exist."
                    })
                    response.status_code = 400
                    return response

                if token.app.client_secret != client_secret:
                    response = JsonResponse({
                        "ok": False,
                        "error": "Client secret incorrect."
                    })
                    response.status_code = 400
                    return response

                if not token.active:
                    response = JsonResponse({
                        "ok": False,
                        "error":
                            "The token is inactive as the user has revoked "
                            "your app's access to their data."
                    })
                    response.status_code = 400
                    return response

                scopes = Scopes()
                for s in required_scopes:
                    if not scopes.check_scope(token.scope.scope_number, s):
                        response = JsonResponse({
                            "ok": False,
                            "error":
                                "The token provided does not have "
                                "permission to access this data."
                        })
                        response.status_code = 400
                        return response

                kwargs['token_type'] = 'oauth'
                kwargs['token'] = token

            elif token_code.startswith('uclapi-'):
                # The token is a generic one, so sanity check
                if personal_data is True:
                    response = JsonResponse({
                        "ok": False,
                        "error": "Personal data requires OAuth."
                    })
                    response.status_code = 400
                    return response

                is_temp_token = False
                try:
                    if token_code.split("-")[1] == "temp":
                        is_temp_token = True
                except IndexError:
                    is_temp_token = False

                if is_temp_token:
                    try:
                        temp_token = TemporaryToken.objects.get(
                            api_token=token_code
                        )
                    except TemporaryToken.DoesNotExist:
                        response = JsonResponse({
                            "ok": False,
                            "error": "Invalid temporary token"
                        })
                        response.status_code = 400
                        return response

                    if request.path != "/roombookings/bookings":
                        temp_token.uses += 1
                        temp_token.save()
                        response = JsonResponse({
                            "ok": False,
                            "error":
                                "Temporary token can only be used "
                                "for /bookings"
                        })
                        response.status_code = 400
                        return response

                    if request.GET.get('page_token'):
                        temp_token.uses += 1
                        temp_token.save()
                        response = JsonResponse({
                            "ok": False,
                            "error":
                                "Temporary token can only return one booking"
                        })
                        response.status_code = 400
                        return response

                    # Check if TemporaryToken is still valid
                    existed = datetime.datetime.now() - temp_token.created

                    if temp_token.uses > 10 or existed.seconds > 300:
                        temp_token.delete()  # Delete expired token
                        response = JsonResponse({
                            "ok": False,
                            "error": "Temporary token expired"
                        })
                        response.status_code = 400
                        return response

                    # This is a horrible hack to force the temporary
                    # token to always return only 1 booking
                    # courtesy: https://stackoverflow.com/a/38372217/825916
                    request.GET._mutable = True
                    request.GET['results_per_page'] = 1

                    temp_token.uses += 1
                    temp_token.save()

                    kwargs['token'] = temp_token
                    kwargs['token_type'] = 'general-temp'

                else:
                    try:
                        token = App.objects.get(
                            api_token=token_code,
                            deleted=False
                        )
                    except App.DoesNotExist:
                        response = JsonResponse({
                            "ok": False,
                            "error": "Token does not exist"
                        })
                        response.status_code = 400
                        return response
                    kwargs['token'] = token
                    kwargs['token_type'] = 'general'

            if 'token_type' not in kwargs:
                raise UclApiIncorrectTokenTypeException

            # Log the API call before carrying it out
            log_api_call(request, kwargs['token'], kwargs['token_type'])

            # Get throttle data
            (
                throttled,
                limit,
                remaining,
                reset_secs
            ) = throttle_api_call(kwargs['token'], kwargs['token_type'])

            if throttled:
                response = JsonResponse({
                    "ok": False,
                    "error": "You have been throttled. "
                             "Please try again in {} seconds."
                             .format(reset_secs)
                })
                response.status_code = 429
                response['X-RateLimit-Limit'] = limit
                response['X-RateLimit-Remaining'] = remaining
                response['X-RateLimit-Retry-After'] = reset_secs
                return response
            else:
                kwargs['X-RateLimit-Limit'] = limit
                kwargs['X-RateLimit-Remaining'] = remaining
                kwargs['X-RateLimit-Retry-After'] = reset_secs

            return view_func(request, *args, **kwargs)
        return wrapped
    return token_scope_check
