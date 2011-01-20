from hashlib import md5

from django import template

register = template.Library()

@register.simple_tag
def avatar(email, size=50, rating='g', default=None):
    """
    Returns a gravatar url.

    Example tag usage: {% avatar user.email 80 "g" %}

    :Parameters:
       - `email`: the email to send to gravatar.
       - `size`: optional YxY size for the image.
       - `rating`: optional rating (g, pg, r, or x) of the image.
       - `default`: optional default image url or hosted image like wavatar.
    """

    rating = rating.lower()
    ratings = ['g', 'pg', 'r', 'x']
    if rating not in ratings:
        raise template.TemplateSyntaxError('rating must be %s' % (
            ", ".join(ratings)))

    hash = md5(email).hexdigest()
    url = 'http://www.gravatar.com/avatar/%s?s=%s&r=%s' % (
        hash, size, rating)
    if default:
        url = "%s&d=%s" % (url, default)
    return url

