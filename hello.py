from datetime import datetime
from mbapi import StudentAPI

def main():
    with StudentAPI('saie.managebac.cn', 443) as client:
        try:
            client.load_session('.session')
        except FileNotFoundError:
            client.token = input('Input token: ')
        my = client.whoami()
        session = client.save_session('.session')
        r = input("HTTP request was successful! would you "
                  "like me to print out\nyour info in a IN-formal tone "
                  "or no? (y/[n]) ")
        if r == 'y':
            print('yay!!!! XD')
            print_friendly(my)
        else:
            print()
            print('Okay... as you wish.')
            print()
            print_formal(my)

        print(end='\n\033[1;31m')
        print("WARNING: your refreshed session key "
              "(starts with {0})"
              .format(session['secret'][:16]))
        print("has been saved to a hidden file here named '.session'.")
        print()
        print("If you wish to no longer use this program, you should")
        print("purge this file to revoke my access to your account.",
              end='\n\033[0m')

def print_friendly(my):
    print('so you are {my[user_nickname]} '
          '(or {my[user_first_name]}) {my[user_last_name]}!'
          .format(my=my))
    print('your chinese name is {my[user_second_name]}'
          .format(my=my))
    signup = datetime.fromtimestamp(my['user_created_at'])
    print('and your account was signed up by the school...')
    print('with your e-mail {my[user_email]} on '
          '{0:%b %d, %Y}!'.format(signup, my=my))
    if my['user_email'] != 'eyzmeng@gmail.com':
        print('cool! pleasure meeting you {}! :D'
              .format(my['user_nickname']))
    else:
        print('[[yay! my part is done :D now you can paste '
              'those guys into the README ^v^]]')

def print_formal(user):
    print('You have been authenticated as '
          '{user[user_nickname]} {user[user_last_name]}, aka '
          '{user[user_second_name]}.'
          .format(user=user))
    signup = datetime.fromtimestamp(user['user_created_at']).astimezone()
    print('Your account was registered with the e-mail '
          '{user[user_email]}\non {0:%b %d, %Y} at {0:%I:%m %p} '
          'in your machine time (offset {0:%z}).'
          .format(signup, user=user))
    if user['user_email'] != 'eyzmeng@gmail.com':
        print('Thank you for your cooperation, {0}. :)'
              .format(user['user_nickname']))
    else:
        print("[[Wait... why didn't YOU respond with yes? >:/]]")

if __name__ == '__main__':
    main()
