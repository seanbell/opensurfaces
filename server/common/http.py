from urlparse import urlparse
import requests


def download(url, binary=False, referer=None):
    """ Download a URL with a fake User-Agent string """

    if not url:
        print "Warning: empty URL"
        return None

    # spoof some headers to make us seem ore like a browser
    headers = {
        'Host': urlparse(url).netloc,
        'User-Agent': (
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/34.0.1847.14 '
            'Safari/537.36'
        ),
        'DNT': '1',
        'Cache-Control': 'max-age=0',
        'Accept-Language': 'en-US,en;q=0.8',
    }

    if referer:
        headers['Referer'] = referer

    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        #print "download success: %s" % url
        if binary:
            return r.content
        else:
            return r.text
    else:
        #print "download fail: (status %s) %s" % (r.status_code, url)
        return None
