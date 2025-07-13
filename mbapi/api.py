"""public API."""
import datetime
import http.cookies
import json
import logging
import re
import urllib

import bs4
import requests

from .util import parse_mime_header


__all__ = ['StudentAPI']

logger = logging.getLogger(__name__)


def _parse_id(prefix, ident):
    if not isinstance(ident, str):
        raise TypeError(f'ID should be a str, not {ident!r}')
    if not ident.startswith(prefix):
        raise ValueError(f'{ident!r} does not start with {prefix!r}')
    id_str = ident[len(prefix):]
    if not id_str.isdigit():
        raise ValueError(f'{ident!r} is not a valid ID')
    return id_str


def _sanitize(s):
    return urllib.parse.quote(s, safe=':')

def _html_from_response(r):
    mtype, params = parse_mime_header(r.headers['Content-Type'])
    if mtype != 'text/html':
        raise ValueError(f'Expected Content-Type to be text/html, '
                         f'received {mtype!r}')
    return r.text

# Python disposes %Z.... WHY
# https://bugs.python.org/msg339672
def _parse_expires(s):
    try:
        # parse HTTP/1.1 "Expires" date, as per RFC2616 Section 14.21
        dt = datetime.datetime.strptime(s, '%a, %d %b %Y %H:%M:%S GMT')
    except ValueError:
        # parse HTTP/1.0 "Expires" date, as per RFC2109 Section 10.1.2
        dt = datetime.datetime.strptime(s, '%a, %d-%b-%Y %H:%M:%S GMT')
    return dt.replace(tzinfo=datetime.timezone.utc)


_EPOCH = datetime.datetime(1970, 1, 1).replace(tzinfo=datetime.timezone.utc)
_SECOND = datetime.timedelta(seconds=1)

def _utc_now():
    return datetime.datetime.now(tz=datetime.timezone.utc)

def _from_epoch(t):
    return datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc)

def _to_epoch(dt):
    if dt.microsecond:
        return dt.timestamp()
    return (dt - _EPOCH) // _SECOND


def _update_dict(old, new):
    """merge, but if there are conflicting values, turn value into list
    (assuming values are homogeneous)

    order in the old dict is preserved.
    only the old dict is updated.
    """
    for key, value in new.items():
        if key not in old:
            old[key] = value
        else:
            # is this multivalued, or are we dealing with a list?
            if isinstance(old[key], list) and not isinstance(new[key], list):
                if not any(value == oldvalue for oldvalue in old[key]):
                    old[key].append(value)
            else:
                if old[key] != value:
                    old[key] = [old[key], value]


class StudentAPI:
    """HTML scraper for student"""

    __slots__ = (
        '_protocol', '_domain', '_port', '_session',
        '_token', '_expires',
    )

    def __init__(self, domain, port=None, protocol='https'):
        self._domain = _sanitize(domain)
        self._protocol = protocol
        if protocol not in {'http', 'https'}:
            raise ValueError(f'Unrecognized protocol: {protocol!r}')
        if port is None:
            port = 443 if protocol == 'https' else 80
        if not isinstance(port, int):
            raise TypeError('port must be an int')
        if not 0 <= port <= 65535:
            raise ValueError('port must be in range 0-65535')
        self._port = port
        self._session = requests.sessions.Session()
        self._token = None
        self._expires = None

    def load_session(self, file):
        with open(file, encoding='ascii') as fp:
            session = json.load(fp)
        self.token = session['secret']
        expires = session.get('expires')
        if expires is not None:
            self.expires = _from_epoch(expires)
        return session

    def save_session(self, file):
        session = dict(secret=self.token,
                       expires=_to_epoch(self.expires)
                               if self.expires is not None
                               else None)
        with open(file, 'w', encoding='ascii') as fp:
            json.dump(session, fp)
        return session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        self._session.close()
        return None

    @property
    def token(self):
        """ManageBac session token.  Must be provided verbatim from
        _managebac_session found in your browser cookie.

        You should set this before making any requests, either
        directly by setting this attribute or indirectly by calling
        load_session().
        """
        return self._token

    @token.setter
    def token(self, token):
        self._token = token
        if token:
            self._session.cookies.set('_managebac_session', token)

    @property
    def expires(self):
        """Token expiration date.  This appears to be useless, as
        the token doesn't actually expire within 0 seconds of a request.
        """
        return self._expires

    @expires.setter
    def expires(self, date):
        self._expires = date

    def has_expired(self, now=None):
        if self._expires is None:
            return True
        return self._expires > (now or _utc_now())

    def get(self, path, check=False, **kwargs):
        """Make an HTTP GET request."""
        logger.info(f'GET {path}')
        base = f'{self._protocol}://{self._domain}:{self._port}'
        url = urllib.parse.urljoin(base, path)
        response = self._session.get(url, **kwargs)

        # update our cookies
        try:
            self._set_cookie(response.headers['Set-Cookie'])
        except KeyError:
            pass

        if check:
            response.raise_for_status()

        return response

    def get_html(self, path, **kwargs):
        response = self.get(path, check=True, **kwargs)
        return _html_from_response(response)

    def _set_cookie(self, rawcookie):
        # cookie jar https://stackoverflow.com/a/21522721
        cookie = http.cookies.SimpleCookie()
        cookie.load(rawcookie)
        token = cookie.get('_managebac_session')
        if isinstance(token, http.cookies.Morsel):
            self.token = token.value
            expires = token.get('expires')
            if isinstance(expires, str):
                self.expires = _parse_expires(expires)

    def get_home_page(self, check=True):
        """GET HTTP request of the student's home page."""
        return self.get('/student/home', check=check)

    def get_home_page_html(self):
        """Using get_home_page(), return the HTML text.
        The response Content-Type is expected to be text/html.
        """
        response = self.get_home_page()
        return _html_from_response(response)

    # there is no get_home_page_json as the data displayed
    # there can be easily retrieved elsewhere

    def whoami(self):
        html_text = self.get_home_page_html()
        dom = bs4.BeautifulSoup(html_text, features='html.parser')
        return _get_current_user(dom)

    def get_my_classes(self, check=True):
        """GET HTTP request for the student's classes."""
        return self.get('/student/classes/my', check=check)

    def get_my_classes_html(self):
        """Using get_my_classes(), return the HTML text.
        The response Content-Type is expected to be text/html.

        If load_external, every pop-up and drop-down menu
        will be loaded.
        """
        response = self.get_my_classes()
        return _html_from_response(response)

    def get_my_classes_json(self, load_external=False):
        html_text = self.get_my_classes_html()
        dom = bs4.BeautifulSoup(html_text, features='html.parser')
        if load_external:
            classes = dom.select_one('#classes')
            for div in classes.find_all('div', recursive=None):
                banner = div.select_one('h4.title')
                popover_icon = div.select_one('span.fusion-popover')
                popover_url = popover_icon['data-hint-url']
                popover_html = self.get_html(popover_url)
                popover_dom = bs4.BeautifulSoup(
                    popover_html, features='html.parser')

                popover_div = dom.new_tag('div',
                                          attrs={'class': ['popover'],
                                                 'hidden': None})
                for elem in popover_dom.children:
                    popover_div.append(elem)
                banner.append(popover_div)
        return student_classes_to_json(dom)

    def get_class_page(self, class_id, check=True):
        """GET HTTP request for front page of a class."""
        return self.get(f'/student/classes/{class_id}', check=check)

    def get_class_page_html(self, class_id):
        """Same as get_class_page(), but return the decoded string.
        The response Content-Type is expected to be text/html.
        """
        response = self.get_class_page(class_id)
        return _html_from_response(response)

    def get_class_page_json(self, class_id):
        """Converts get_class_page_html() into HTML."""
        page = self.get_class_page_html(class_id)
        return student_class_page_to_json(page)


def student_classes_to_json(html_text):
    if isinstance(html_text, bs4.BeautifulSoup):
        dom = html_text
    else:
        dom = bs4.BeautifulSoup(html_text, features='html.parser')
    response = {}
    response['whoami'] = _get_current_user(dom)

    response['classes'] = classes = []
    for div in dom.select_one('#classes').find_all('div', recursive=False):
        class_json = {}
        try:
            class_json['class_id'] = _parse_id('ib_class', div['id'])
        except (KeyError, ValueError):
            pass

        info_div = div.select_one('div.ib-class-row')
        _update_class_info(class_json, info_div)

        unit_div = div.select_one('div.units-container')
        if unit_div and unit_div.children:
            _update_class_units(class_json, unit_div)

        task_div = div.select_one('div.tasks-container')
        if task_div and task_div.contents:
            _update_class_tasks(class_json, task_div)

        upds_div = div.select_one('div.updates-container')
        if upds_div and upds_div.contents:
            _update_class_updates(class_json, upds_div)

        classes.append(class_json)
    return response


def _update_class_info(class_json, div):
    icon = div.select_one('img.sebo-icon')
    class_json['class_icon'] = icon['src']

    banner = div.select_one('h4.title')
    title = banner.a
    # if you see the 2 on a separate line and want to
    # know why..... i don't know either. but it COULD be
    # their way of dealing with the same course,
    # only taught by different teachers.
    #
    # for us though.... we'll keep it simple
    class_json['class_name'] = title.text.strip()
    class_json['class_url'] = title['href']

    # get # units, # tasks, # updates from the dropdown menu
    dropdown = div.select_one('div.class-dropdown')
    stats = {}
    for item in dropdown.select('div.class-dropdown-item'):
        val = item.select_one('div.number').text
        cat = item.select_one('div.text').text
        stats[cat.lower()] = val
    if stats:
        class_json['class_stats'] = stats

    # now return to the teachers, which are available as tiny avatars
    # like the sidebar we've dealt with in student_class_page_to_json().
    #
    # this, unfortunately, does not have a very descriptive name.
    teachers = dropdown.select_one('div.flex-start')
    if teachers is not None:
        # let's see if we hit the jackpot - this giant pop-up
        # HTML seems to appear in the data-hint attribute, which
        # we will parse that instead as it has the complete list.
        # (again, the class name makes no sense.)
        jackpot = teachers.select_one('span.user-link > div')
        if jackpot is not None:
            value = jackpot['data-hint']
            teaches = bs4.BeautifulSoup(value, features='html.parser').table
        else:
            teaches = teachers

        teacher_list = []
        for teach in teaches.children:
            if not isinstance(teach, bs4.Tag):
                continue
            teacher_json = {}
            avatar = teach.select_one('div.avatar')
            # and yes, somehow you get 'span's on the outside
            # while the pop-up HTML uses a table of rows of 'div's.
            # (i am actually losing my sanity over weird s**t like this)
            if teach.name == 'span':
                # hmm... this is curious.
                # i suppose the JavaScript turns this into
                # data-original-title on my browser, but this
                # really is just 'title'
                title = (teach.get('title') or
                         teach.get('data-original-title'))
                if title is not None:
                    teacher_json.update(parse_user_name(title))
            elif teach.name == 'tr':
                if avatar is not None:
                    sibling = avatar.next_sibling.strip()
                    teacher_json.update(parse_user_name(sibling))
            if avatar is not None:
                teacher_json.update(parse_user_avatar(avatar))
            teacher_list.append(teacher_json)

        class_json['class_teachers'] = teacher_list

    # if load_external was set to True, we may scrape from the
    # popover box the teachers, the subject, and # of students
    popover = banner.select_one('div.popover')
    if popover:
        # ... although that is yet to be implemented now.
        pass


def _update_class_units(class_json, div):
    pass


def _update_class_tasks(class_json, div):
    pass


def _update_class_updates(class_json, div):
    pass


def student_class_page_to_json(html_text):
    dom = bs4.BeautifulSoup(html_text, features='html.parser')
    response = {}
    response['whoami'] = _get_current_user(dom)

    content = dom.select_one('div.content-block')
    response['class'] = _get_class_basic_info(content)

    section = dom.select_one('section.js-members-section')
    teachers = section.select_one('div.teachers-list')
    if teachers is not None:
        list_t = [parse_teacher_element(div) for div
                  in teachers.select('div.member')]
    else:
        list_t = None

    students = section.select_one('div.students-list')
    list_s = [parse_student_element(div) for div
              in students.select('div.member')]

    response['teachers'] = list_t
    response['students'] = list_s

    return response


# only in SAIE - first (NICK) last | second
# (we will be as greedy as possible and include spaces since
# they are clearly machine generated)
RE_NAME = re.compile(r'\A(.+) \((.+)\) (.+) \| (.+)\Z')

def parse_user_name(name):
    """Parse a user's name and return a dict with certain fields set.
    If the regular expression fails to match, then only 'user_name'
    will be set.  Otherwise, four additional fields would be set:

      *  user_first_name & user_last_name
      *  user_nickname (name in parenthesis)
      *  user_second_name (name after vertical bar)
    """
    user = {}
    match = RE_NAME.match(name)
    if match:
        (
            user['user_first_name'],
            user['user_nickname'],
            user['user_last_name'],
            user['user_second_name'],
        ) = match.groups()
    user['user_name'] = name
    return user


RE_JS_CDATA = re.compile(r'//<!\[CDATA\[\n(.*)\n//\]\]>', flags=re.DOTALL)
# to be absolutely sure, anchor the closing brace of the
# function defined to be LOU_init
RE_LOU_ID = re.compile(
    r'LOU\.identify\(\'(\d+)\', (\{.+\})\)\s+\}\Z', flags=re.DOTALL)


def _get_current_user(dom):
    student_json = {}
    # extract info from CDATA, if possible
    for script in reversed(dom.select('script')):
        match = RE_JS_CDATA.search(script.text)
        if not match:
            continue
        lou_data = match.group(1).strip()
        match = RE_LOU_ID.search(lou_data)
        if not match:
            continue
        student_id, student_auth = match.groups()

        # please be valid JSON
        _update_dict(student_json, json.loads(student_auth))
        student_json['user_id'] = student_id
        break

    # extract from zendesk widget, if possible
    zendesk = dom.select_one('div#zendesk-widget')
    zendesk_json = {}
    if zendesk is not None:
        try:
            zendesk_json['user_email'] = zendesk['data-email']
        except KeyError:
            pass

        try:
            zendesk_json['user_role'] = zendesk['data-role']
        except KeyError:
            pass

        try:
            name = zendesk['data-user']
        except KeyError:
            pass
        else:
            zendesk_json.update(parse_user_name(name))

    _update_dict(student_json, zendesk_json)

    # extract from <body> and <title> - though it's probably just
    # cross-validation up to this point
    meta_json = {}
    body = dom.body
    assert body is not None
    user_id = body.get('data-user-id') or body.get('data-airbrake-user-id')
    if user_id is not None:
        meta_json['user_id'] = user_id

    # might find the name in title as well
    title = dom.head.title
    if title is not None:
        name = title.text.removeprefix('ManageBac |').strip()
        meta_json.update(parse_user_name(name))

    navbar = dom.select_one('div.navbar.navbar-collapse')
    if navbar is not None:
        profile = navbar.select_one('div.profile-link')
        avatar_div = profile.select_one('div.avatar')
        meta_json['user_avatar'] = parse_user_avatar(avatar_div)

    _update_dict(student_json, meta_json)
    return student_json


def _get_class_basic_info(content):
    """parse class name & ID from div.content-block.
    this seems to only show up in /students/classes/<CLASS_ID>.
    how generally this function can be used for is yet unknown.
    """
    class_json = {}
    header = content.select_one('div.content-block-header')
    class_json['class_name'] = header.text.strip()

    # the last div inside .content-block seems to be
    # often marked by the id "ib_class_<DIGITS>"
    #
    # does this always happen? i don't know. but then
    # again it's hard to say i know a better way.
    last = content.find_all('div', recursive=False)[-1]
    try:
        class_id = _parse_id('ib_class_', last['id'])
    except (KeyError, ValueError):
        class_id = None
    if class_id is not None:
        class_json['class_id'] = class_id

    return class_json


# note that a teacher element and a student element hold
# the title attribute (which contains a person's name)
# on two levels: for a student, the title can be directly
# extracted from the member div itself.  but the same info
# is only accessible for teacher through this quirky inner
# div called 'js-selection-owner'.... luckily the avatar
# in both cases can be processed in a similar fashion.
#
# div.info (together with the spurious .stretch class) is
# exclusive to teachers, so we will just process them here.

def parse_teacher_element(member):
    holder = member.select_one('div.js-section-owner')
    holder_json = _parse_user_container(holder)

    info = member.select_one('div.info')
    name = info.select_one('div.user-name')
    extra = info.select_one('ul.extra')

    info_json = {}
    if name is not None:
        if name.a is not None:
            info_json['user_url'] = name.a['href']
        info_json['user_name'] = name.text

    if extra is not None:
        for item in extra.find_all('li'):
            resource = item.a['href']
            if resource.startswith('tel:'):
                info_json['user_tel'] = item.a.text
            elif resource.startswith('mailto:'):
                info_json['user_email'] = item.a.text
            else:
                raise ValueError(f'unknown resource URI: {resource!r}')

    _update_dict(holder_json, info_json)
    return holder_json


def parse_student_element(member):
    # div.member itself IS the data holder
    holder_json = _parse_user_container(member)
    return holder_json


def _parse_user_container(div):
    holder_json = {}

    try:
        holder_json.update(parse_user_name(div['title']))
    except KeyError:
        pass

    try:
        # students don't have this, but that's okay;
        # we may steal this from the avatar instead.
        holder_json['user_id'] = div['data-author-id']
    except KeyError:
        pass

    avatar_div = div.select_one('div.avatar')
    if avatar_div is not None:
        holder_json['user_avatar'] = parse_user_avatar(avatar_div)

    # copy user_id for convenience, if we found it in avatar
    holder_user_id = (holder_json.get('user_id') or
                      holder_json['user_avatar']['user_id'])
    if holder_user_id is not None:
        holder_json['user_id'] = holder_user_id

    return holder_json


RE_THM_URL = re.compile('background-image: url\(([^\)]*)\);?')

# this is a pretty standard div structure used throughout the system
#
# the CSS classes of the avatar won't be stored, but i will still talk
# a little bit about this.
#
#     div.avatar.online        so far i have only seen my own pfp with this
#     div.avatar.tiny          used in the member list
#     div.avatar.tiny.empty    displays data-initials with ::before
#                              (still uses tiny_* images!)
#     div.avatar.micro         used in assignment lists
#     div.avatar.micro.empty   functions likewise

def parse_user_avatar(div):
    assert div.name == 'div', div
    assert 'avatar' in div['class'], div

    avatar_json = {}
    if 'empty' in div['class']:
        avatar_json['avatar_url'] = None
    else:
        url_match = RE_THM_URL.search(div['style'])
        assert url_match is not None
        avatar_json['avatar_url'] = url_match.group(1)

    avatar_json['user_initials'] = div['data-initials']
    avatar_json['user_id'] = div['data-id']

    return avatar_json
