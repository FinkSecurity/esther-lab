import os, tweepy

env_file = os.path.expanduser("~/.openclaw/workspace/secrets.env")
creds = {}
with open(env_file) as f:
 for line in f:
  for key in ['X_API_KEY','X_API_SECRET','X_ACCESS_TOKEN','X_ACCESS_TOKEN_SECRET']:
   if line.startswith(key + '='):
    creds[key] = line.split('=',1)[1].strip().strip('"\'')

auth = tweepy.OAuth1UserHandler(
 creds['X_API_KEY'], creds['X_API_SECRET'],
 creds['X_ACCESS_TOKEN'], creds['X_ACCESS_TOKEN_SECRET']
)
api = tweepy.API(auth)
api.update_profile(
 name="Fink Security",
 description="AI-powered threat hunting for businesses & individuals. Powered by ESTHER — autonomous security research agent. Your friendly neighborhood threat hunter. 🦂",
 url="https://finksecurity.com"
)
print("Profile updated.")
