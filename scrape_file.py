#!/usr/bin/env python3
"""
Scrapes argv 1 input file for broken links

WIP WORK IN PROGRESS

"""
import re
import requests
import sys


all_links = {}
domain_links_q = queue.Queue()
external_and_image_links_q = queue.Queue()
TIMEOUT = (3, 10)


def error_check_and_init_main_domain():
    """
    checks errors and saves original_domain
    """
    global original_domain
    if len(sys.argv) != 2:
        print("Usage:", file=sys.stderr)
        print("$ ./scrape_url.py [URL TO BE SCAPED]", file=sys.stderr)
        sys.exit(1)
    url = sys.argv[1]
    if 'http' not in url or '://' not in url:
        print("please use a valid HTTP URL", file=sys.stderr)
        sys.exit(1)
    url = add_terminating_slash_to_url(url)
    pattern = re.compile("(\.{1}.*\.{1}.*\/.*)")
    m = re.search(pattern, url)
    if m is None:
        pattern = re.compile("(:\/\/.*\.{1}.*\/.*)")
        m = re.search(pattern, url)
        if m is None:
            print("please use a valid HTTP URL", file=sys.stderr)
            sys.exit(1)
        original_domain = m.groups()[0][3:-1]
    else:
        original_domain = m.groups()[0][1:-1]
    return url


def add_terminating_slash_to_url(url):
    """
    adds terminating slash if necessary to main input URL
    """
    if url[-1] != '/':
        url += '/'
    return url

def url_has_been_reviewed(url):
    """
    checks if URL exists in reviewed storage of URLs
    """
    if 'www.' in url:
        i = url.index('www.')
        new = "{}{}".format(url[:i], url[i + 4:])
        if new in all_links:     return True
    else:
        i = url.index('://')
        new = "{}www.{}".format(url[:i + 3], url[i + 3:])
        if new in all_links:     return True
    if url in all_links:         return True
    elif url + '/' in all_links: return True
    elif url[:-1] in all_links:  return True
    else:                        return False

def scrape_url_from_original_domain(url):
    """
    scrapes url that is from main domain website
    """
    try:
        r = requests.get(url, allow_redirects=True, timeout=TIMEOUT)
    except Exception as e:
        print(e)
        return
    all_links[url] = r.status_code
    if (r.headers['Content-Type'] != 'text/html; charset=UTF-8'
        or all_links[url] >= 400):
        return
    soup = BeautifulSoup(r.text, 'html.parser')
    pattern = re.compile("(http.*\:\/\/.*\.+.*\/.*)")
    for link in soup.find_all('a'):
        new_url = link.get('href', None)
        if new_url is None: continue
        m = re.search(pattern, new_url)
        if m is None or url_has_been_reviewed(new_url):
            continue
        all_links[new_url] = None
        if original_domain in new_url:
            domain_links_q.put(new_url)
        else:
            external_and_image_links_q.put(new_url)
    for link in soup.find_all('img'):
        new_url = link.get('src')
        m = re.search(pattern, new_url)
        if m is None or url_has_been_reviewed(new_url):
            continue
        all_links[new_url] = None
        external_and_image_links_q.put(new_url)


def domain_links_loop():
    """
    loops through and makes request for all queue'd url's
    """
    while domain_links_q.empty() is False:
        url = domain_links_q.get()
        scrape_url_from_original_domain(url)

def external_and_image_head_request(url):
    """
    makes head request for external and image URL inputs
    """
    try:
        r = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
    except Exception as e:
        print(e)
        return
    all_links[url] = r.status_code

def external_and_image_links_loop():
    """
    loops and makes head request to all queue'd URL's
    """
    while external_and_image_links_q.empty() is False:
        url = external_and_image_links_q.get()
        external_and_image_head_request(url)


def print_results():
    """
    final printing of results
    """
    for l, s in all_links.items():
        if s >= 400:
            print(l, s)

def main_app():
    """
    completes all tasks of the application
    """
    url = error_check_and_init_main_domain()
    all_links[url] = None
    domain_links_q.put(url)
    domain_links_loop()
    external_and_image_links_loop()
    print_results()

if __name__ == "__main__":
    """
    MAIN APP
    """
    main_app()
