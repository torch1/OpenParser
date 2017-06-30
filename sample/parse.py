from bs4 import BeautifulSoup
import bs4
import requests
import re
import sys
import json
from urlparse import urljoin, urlparse
from Queue import Queue

email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
phone_regex = re.compile(r"(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?")

class Webpage:
    def __init__(self, html, url):
        self.html = html
        self.url = url

    def parse(self):
        soup = BeautifulSoup(self.html, "lxml")

        strings = [string for string in soup.strings]

        # find links
        _found_links = []
        def merge(url):
            _found_links.append(url)
            return urljoin(self.url, url)
        links = [{"url": merge(a['href']), "name": _scrub(a.text) if _scrub(a.text) else a['href']} for a in soup.find_all("a") if a.get('href') is not None and a.get('href') is not "#" and a.get("href").startswith("mailto:") is not True and a.get("href") not in _found_links]

        # find social media
        social_media = {}
        _social_media_sites = ["facebook.com", "youtube.com", "twitter.com", "linkedin.com", "github.com", "plus.google.com"]
        _social_media_urls = []
        for link in links:
            for site in _social_media_sites:
                if site in link['url'].lower() and link['url'] not in _social_media_urls:
                    if site not in social_media:
                        social_media[site] = []
                    social_media[site].append(link)
                    _social_media_urls.append(link['url'])
        del _social_media_sites, _social_media_urls

        # find description
        description = (soup.find('meta', attrs={'name':'og:description'}) or soup.find('meta', attrs={'property':'description'}) or soup.find('meta', attrs={'name':'description'}))
        if description is not None:
            description = description.get("content")

        # find telephone numbers
        telephones = []
        i = 0
        for string in strings:
            for match in phone_regex.finditer(string):
                extended = _get_desc_phone(strings, i)
                number = match.group(0)
                if len(match.string) > 100: # or _alpha_ratio(match.string) > 0.4:
                    break
                if ("EIN" in match.string or "EIN" in extended) and ("tax" in match.string or "tax" in extended):
                    continue
                if extended == match.string:
                    if not len(_alpha(extended.replace(number, "")).strip()) > 0:
                        extended = None
                if extended.endswith(number):
                    extended = extended[:-(len(number))].strip()
                if match.string is None:
                    continue
                telephones.append({
                    "number": number,
                    "extended": extended
                })
                break
            i += 1

        # find emails
        emails = []
        _emails_alone = []
        for email in [email for email in soup.find_all("a") if email.get("href") is not None and email.get("href").startswith("mailto:") is True]:
            if email.get('href').startswith("mailto:"):
                email_address = email.get("href")[7:]
                if email_address in _emails_alone:
                    continue
                email_description = _get_desc(email, minwords=4, maxlevels=2, doesnt_include=email_regex, repl=email_address)
                emails.append({
                    "address": email_address,
                    "extended": _scrub(email_description)
                })
                _emails_alone.append(email_address)
        for string in [s for s in strings if email_regex.match(s)]:
            for match in email_regex.finditer(string):
                if match.string not in _emails_alone:
                    _emails_alone.append(match.string)
                    emails.append({
                        "address": match.string,
                        "extended": string
                    })
        del _emails_alone # might as well, save memory
        return {
            "links": links,
            "social_media": social_media,
            "description": description,
            "telephones": telephones,
            "emails": emails
        }

def _get_desc_phone(strings, i):
    extended = strings[i]
    if len(re.sub(phone_regex, "", extended).strip()) > 0:
        return extended
    j = i - 1
    while len(extended) < 100:
        try:
            previous = strings[j]
            if not phone_regex.match(previous): # if there is a phone number in the extended text, we are probably outside the relevant boundary
                extended = strings[j] + " " + extended
            else:
                break
        except IndexError:
            break
        j -= 1
    extended = _scrub(extended)
    if _alpha_ratio(extended) < 0.5:
        return strings[i]
    return extended

def _get_desc(element, minwords=3, maxlength=140, maxlevels=3, doesnt_include=None, repl=""):
    levels = 0
    desc = element.getText()
    previous = element
    while len(desc.split(" ")) <= minwords and levels <= maxlevels:
        if previous is None:
            break
        new_desc = previous.getText(separator=u' ')
        if doesnt_include is not None and doesnt_include.match(new_desc.replace(repl, "")):
            break
        if _alpha_ratio(new_desc) < 0.7:
            break
        desc = new_desc
        if len(previous.parent.text) > len(previous.text)*8:
            previous = previous.previousSibling
            while isinstance(previous, bs4.element.NavigableString):
                previous = previous.previousSibling
        else:
            previous = previous.parent
        levels += 1
    if len(desc) > maxlength:
        return "..." + desc[-maxlength:]
    return desc

def _scrub(string):
    string = string.strip()
    string = string.replace(" , ", ", ")
    string = string.replace("\\n", " ")
    if string.startswith(", "):
        string = string[2:]
    while "  " in string:
        string = string.replace("  ", " ")
    return string.strip()

def webpage_from_url(url):
    return Webpage(requests.get(url).text, url)

def _alpha_ratio(string):
    only = _alpha(string)
    ratio = len(only) / (len(string) + 0.01)
    return ratio

def _alpha(string):
    only = re.sub(r'\W+', '', string)
    return only

# simple alias for constructor
def webpage_from_text(html, url=""):
    return Webpage(html, url)

def recursive_parse(url, verbose=False, max_depth=4, local=True):
    hostname = urlparse(url).hostname
    if verbose:
        print "Recursively parsing site with max depth of " + str(max_depth) + " @ " + url
    responses = []
    queue = Queue()
    queue.put((0, url))
    seen_urls = []
    while queue.qsize() > 0:
        level, url = queue.get()
        seen_urls.append(url.lower())
        if verbose:
            print '  ' + (" "*level) + " - " + url
        response = webpage_from_url(url).parse()
        responses.append(response)
        if level + 1 <= max_depth:
            for link in response['links']:
                href = link['url']
                if url.lower() not in seen_urls:
                    if (not local) or (urlparse(link['url']).hostname == hostname):
                        queue.put((level + 1, link['url']))
                        seen_urls.put(link['url'].lower())
    # todo: merge

if len(sys.argv) is not 0:
    if len(sys.argv) >= 2:
        data = None
        if "--recursive" in sys.argv:
            data = recursive_parse(sys.argv[1], verbose=True)
        else:
            data = webpage_from_url(sys.argv[1]).parse()
        if "--json" in sys.argv:
            print json.dumps(data, indent=4)
        else:
            print "OpenParser (a Torch project) // licensed GPLv3"
            print "Parsed: " + sys.argv[1]
            if data['description']:
                print "> " + data['description']
            print "========= LINKS ========="
            for link in data['links']:
                print ' '*4 + link['name']
                print ' '*8 + link['url']
            print
            print "===== SOCIAL MEDIA ====="
            for sites in data['social_media'].values():
                for site in sites:
                    print ' '*4 + site['name']
                    if site['name'] != site['url']:
                        print ' '*8 + site['url']
            print
            print "===== TELEPHONES ====="
            for telephone in data['telephones']:
                if telephone['extended']:
                    print ' '*4 + telephone['extended'].replace("\n", " / ")
                print ' '*8 + telephone['number'].replace("\n", " / ")
            print
            print "===== EMAILS ====="
            for email in data['emails']:
                print ' '*4 + email['extended'].replace("\n", " / ")
                if email['address'] != email['extended']:
                    print ' '*8 + email['address'].replace("\n", " / ")
    else:
        print "please pass in a URL as the first argument!"
