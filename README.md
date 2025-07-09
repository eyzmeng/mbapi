# mbapi - a ManageBac "API" for students

(as pretty as that sounds, this is just an elaborate web scraper
made with Python requests and BeautifulSoup dom selector.
either way, i still hate school, so here you go GitHub.)

easy installation:

    pip install git+https://github.com/eyzmeng/mbapi.git
    curl -O https://raw.githubusercontent.com/eyzmeng/mbapi/main/hello.py

pip is whatever ur python package manager is called
(pip3, python3 -m pip, etc...)

installation in case i feel bad for leaving any trace
on ur computer:

    git clone https://github.com/eyzmeng/mbapi.git
    cd mbapi
    python -m venv venv

    either one of:
      source  venv/bin/activate  [*nix shell]
      venv\Scripts\activate.bat  [Windows cmd.exe]
      venv\Scripts\Activate.ps1  [Windows Powershell]

    pip install -e .

    [[then i can do rm -rf mbapi or equivalent when i'm done...]]

## test your stuff!

run hello.py!

it'll prompt you for a token, and that can be obtained by
opening your browser dev tools, hunt down any request with
the `_managebac_session` token (it's often easier to refresh
the whole page with the tab open), and YEET it out of the
browser - okay you get what i mean

you can choose between a friendly voice, like this!

    you are Ethan (or Yizheng) Meng!
    your chinese name is 蒙以正
    and your account was signed up by the school...
    with your e-mail eyzmeng@gmail.com on Jun 06, 2023!

or a boring monotone voice, like this...

    You have been authenticated as Ethan Meng, aka 蒙以正.
    Your account was registered with the e-mail eyzmeng@gmail.com
    on Jun 06, 2023 at 08:06 AM in your machine time (offset +0800).

(which is the default, sadly... the world we live in...)

but you can choose! and that's all that matters :)

## IMPORTANT: SECURITY STUFF

remember to keep the token SECRET, as ANYONE in this world
with that token can access your account. luckily the token
you put in is only ever written to a file named `.session`,
so just delete the file and you would've effectively revoked
all access to your account :)

you'll also see a warning message if you run the code too,
which i'll put up here tooooo...

    WARNING: your refreshed session key (starts with [...])
    has been saved to a hidden file here named '.session'.

    If you wish to no longer use this program, you should
    purge this file to revoke my access to your account.

## trivia (and maybe how to actually use this code)

(writing this since i've graduated HS for a year...)

to my knowledge there are only two people who have run this
script (me and someone whom i am relatively closer to than
the rest of the class (and the entire school in general)).
hello.py worked for both of our accounts so take whatever
you like from it (i only tested this once on that someone
else's browser since... well you can imagine how awkward
it was asking him about it!  If you have a problem with how
little this was tested and developed then how about you *try*
to talk to people as an introvert!!!)

i forgot if i ever shared what my school was but seeing that it
*probably* doesn't matter (and the intrepid soul who dares to use
this deserves better than just the vague quirky name "ManageBac"):
it was [saie.managebac.cn](https://saie.managebac.cn/).  if that
looks like the grading system your school uses, this script will
probably work on that.  (Of course, you likely won't be able to
log in since it's kind of an internal-school-thing.  well neither
can i, but i can provide HTMLs i captured if you ask me :P)

and at last... why am i doing this, you may ask.  well this gets
a bit "personal", but let's just say... i don't like being treated
as "less" than capable of speaking English and having my name
that is technically not a legal name but i've been called by for
long enough that it might as well be my real name, being treated
as less than a "real name" -- like a joke "English" name exclusively
as a device for derision and condescension and can't be seen
actually being called that name in serious situations.

also having to confront the profile picture as a face of me is
disgusting it surely gave me nightmares ugh i hate school (well
at least i wish paying for the tuition meant that they'd care
enough to give us an email at their NetEase enterprise
[usapschool.com][] mail domain... it's like they don't even try smh)

[usapschool.com]: http://www.usapschool.com/ "Yes, you read the URL right.  You won't access it with http://usapschool.com/ alone since the domain doesn't resolve.  And don't even try HTTPS because their server's too dumb for a SSL handshake.  Right now they are most concerned with advertising themselves on Weixin shorts and stories/columns/whatever those articles are called.  And I hope it stays that way."
