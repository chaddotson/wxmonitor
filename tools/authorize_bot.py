import twython

app_key = input("Your app key: ")
app_secret = input("Your app secret: ")

twitter = twython.Twython(app_key, app_secret)

auth = twitter.get_authentication_tokens()

print("Log into Twitter as the user you want to authorize and visit this URL:")
print("\t" + auth['auth_url'])

pin = input("Enter your PIN: ")

twitter = twython.Twython(app_key, app_secret, auth['oauth_token'], auth['oauth_token_secret'])
tokens = twitter.get_authorized_tokens(pin)

print("Your token: " + tokens['oauth_token'])
print("Your token secret: " + tokens['oauth_token_secret'])