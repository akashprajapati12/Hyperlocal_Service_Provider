from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

class TabSessionMiddleware(SessionMiddleware):
    """
    Middleware that enables multiple active user sessions across different browser tabs.
    It identifies browser tabs via a unique 'tab' query parameter or the Referer header,
    and isolates sessions by appending the tab identifier to the session cookie name.
    """
    def process_request(self, request):
        tab_id = request.GET.get('tab') or request.POST.get('tab')
        if not tab_id:
            referer = request.META.get('HTTP_REFERER')
            if referer:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(referer)
                queries = parse_qs(parsed.query)
                tab_id = queries.get('tab', [None])[0]

        # Determine dynamic cookie name
        cookie_name = f"{settings.SESSION_COOKIE_NAME}_{tab_id}" if tab_id else settings.SESSION_COOKIE_NAME
        request.session_cookie_name = cookie_name

        # Perform the standard Django SessionMiddleware process with the dynamic cookie name
        session_key = request.COOKIES.get(cookie_name)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        # Delegate first to Django's standard process_response
        response = super().process_response(request, response)

        # Retrieve the dynamic cookie name set during request processing
        cookie_name = getattr(request, 'session_cookie_name', settings.SESSION_COOKIE_NAME)

        # If the response is a redirect, automatically append the tab parameter to the redirect Location URL
        if response.status_code in (301, 302, 303, 307, 308) and 'Location' in response:
            tab_id = request.GET.get('tab') or request.POST.get('tab')
            if not tab_id:
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(referer)
                    queries = parse_qs(parsed.query)
                    tab_id = queries.get('tab', [None])[0]
            
            if tab_id:
                location = response['Location']
                # Check if location is same-origin or relative
                if location.startswith('/') or location.startswith(request.build_absolute_uri('/')[:-1]):
                    from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
                    parsed_loc = urlparse(location)
                    queries = parse_qsl(parsed_loc.query)
                    # Only append if not already present
                    if not any(k == 'tab' for k, v in queries):
                        queries.append(('tab', tab_id))
                        new_query = urlencode(queries)
                        # Rebuild the redirect location
                        response['Location'] = urlunparse((
                            parsed_loc.scheme,
                            parsed_loc.netloc,
                            parsed_loc.path,
                            parsed_loc.params,
                            new_query,
                            parsed_loc.fragment
                        ))

        if cookie_name != settings.SESSION_COOKIE_NAME:
            # If default cookie was set by super().process_response, rename it to the dynamic one
            if settings.SESSION_COOKIE_NAME in response.cookies:
                cookie_val = response.cookies[settings.SESSION_COOKIE_NAME]
                response.cookies[cookie_name] = cookie_val
                
                # Copy all cookie attributes (max-age, path, domain, secure, httponly, samesite, etc.)
                response.cookies[cookie_name]['path'] = cookie_val['path']
                response.cookies[cookie_name]['domain'] = cookie_val['domain']
                response.cookies[cookie_name]['secure'] = cookie_val['secure']
                response.cookies[cookie_name]['httponly'] = cookie_val['httponly']
                response.cookies[cookie_name]['expires'] = cookie_val['expires']
                response.cookies[cookie_name]['max-age'] = cookie_val['max-age']
                response.cookies[cookie_name]['samesite'] = cookie_val['samesite']

                # Delete the default cookie to prevent session leakage/pollution
                del response.cookies[settings.SESSION_COOKIE_NAME]

        return response
