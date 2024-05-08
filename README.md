# mbapi - an "API" for us mortal students

easy installation:

    pip install git+http://git.rapidcow.org/mbapi
    curl -O http://git.rapidcow.org/mbapi/plain/hello.py

pip is whatever ur python package manager is called
(pip3, python3 -m pip, etc...)

installation in case i feel bad for leaving any trace
on ur computer:

    git clone http://git.rapidcow.org/mbapi
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
