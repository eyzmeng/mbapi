from datetime import datetime
from rdks.mbapi import StudentAPI

with StudentAPI('saie.managebac.cn', 443) as client:
    try:
        client.load_session('.session')
    except FileNotFoundError:
        client.token = input('Input token: ')
    my = client.whoami()
    client.save_session('.session')
    print('hi! i am {my[user_nickname]} '
          '(or {my[user_first_name]}) :D'
          .format(my=my))
    print('my chinese name is {my[user_second_name]}...'
          .format(my=my))
    signup = datetime.fromtimestamp(my['user_created_at'])
    print('and my account was signed up by my school on '
          '{0:%b %d, %Y}!'.format(signup))
