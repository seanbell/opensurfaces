import urllib2
import lxml.html

from django.db import models
from django.utils.timezone import now


class License(models.Model):
    added = models.DateTimeField(default=now)

    name = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=255, blank=True)

    # creative commons info
    creative_commons = models.BooleanField(default=False)
    cc_attribution = models.BooleanField(default=False)
    cc_noncommercial = models.BooleanField(default=False)
    cc_no_deriv = models.BooleanField(default=False)
    cc_share_alike = models.BooleanField(default=False)

    # True if you can publish a result derived from this photo without having
    # to get permission or use creative commons on the derived work
    publishable = models.BooleanField(default=False)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return self.url

    def publishable_score(self):
        """ Return a score indicating how 'open' the photo license is """
        score = 0
        if self.creative_commons:
            if not self.cc_attribution:
                score += 1
            if not self.cc_noncommercial:
                score += 2
            if not self.cc_no_deriv:
                score += 10
            if not self.cc_share_alike:
                score += 2
        return score

    @staticmethod
    def get_for_blendswap_scene(blendswap_id):
        """ Return (license, blendswap url, blendswap username) """

        blendswap_url = 'http://www.blendswap.com/blends/view/%s' % blendswap_id
        print 'Visiting %s...' % blendswap_url

        try:
            response = urllib2.urlopen(blendswap_url).read()
        except urllib2.URLError as e:
            if e.code == 404:
                license, _ = License.objects.get_or_create(name='All Rights Reserved')
                return license, None, None
            else:
                return None, None, None

        html = lxml.html.fromstring(response)
        blendswap_username = html.find_class("user_link")[0].text_content().strip()

        for element, attribute, link, pos in html.iterlinks():
            if (attribute and link and attribute.lower() == 'href' and
                    (link.startswith('http://creativecommons.org/licenses/') or
                     link.startswith('http://creativecommons.org/publicdomain/')) and
                    link.endswith('/')):
                license, _ = License.objects.get_or_create(
                    creative_commons=True, url=link)
                return license, blendswap_url, blendswap_username

        raise ValueError("Could not find license")

    @staticmethod
    def get_for_flickr_photo(flickr_user, flickr_id):
        """ Return license instance """

        try:
            response = urllib2.urlopen(
                'http://www.flickr.com/photos/%s/%s/' %
                (flickr_user, flickr_id)
            ).read()
        except urllib2.URLError as e:
            if e.code == 404:
                return License.objects.get_or_create(
                    name='All Rights Reserved')[0]
            else:
                return None

        html = lxml.html.fromstring(response)
        for element, attribute, link, pos in html.iterlinks():
            if (attribute and link and attribute.lower() == 'href' and
                    link.startswith('http://creativecommons.org/licenses/') and
                    link.endswith('/')):
                return License.objects.get_or_create(
                    creative_commons=True,
                    url=link)[0]

        #for element, attribute, link, pos in html.iterlinks():
            #if (attribute and link and attribute.lower() == 'href' and
                #link.endswith('/help/general/#147')):
                #return License.objects.get_or_create(
                        #name='All Rights Reserved')[0]

        return License.objects.get_or_create(
            name='All Rights Reserved')[0]
