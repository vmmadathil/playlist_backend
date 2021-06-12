import base64, json, requests, os


#Add your client ID
CLIENT_ID = os.getenv('CLIENT_ID')

#aDD YOUR CLIENT SECRET FROM SPOTIFY
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

#Port and callback url can be changed or left to localhost:5000
PORT = "5000"
CALLBACK_URL = "http://localhost:8888/callback/"

#Add needed scope from spotify user
SCOPE = 'user-library-read user-top-read playlist-modify-public playlist-read-private'
#token_data will hold authentication header with access code, the allowed scopes, and the refresh countdown 
TOKEN_DATA = []

SPOTIFY_URL_AUTH = 'https://accounts.spotify.com/authorize/?'
SPOTIFY_URL_TOKEN = 'https://accounts.spotify.com/api/token/'
RESPONSE_TYPE = 'code'   
HEADER = 'application/x-www-form-urlencoded'
REFRESH_TOKEN = ''
    
    
def getAuth(client_id, redirect_uri, scope):
    data = "{}client_id={}&response_type=code&redirect_uri={}&scope={}".format(SPOTIFY_URL_AUTH, client_id, redirect_uri, scope) 
    return data

def getToken(code, client_id, client_secret, redirect_uri):
    body = {
        "grant_type": 'authorization_code',
        "code" : code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }

    auth_str = '{}:{}'.format(CLIENT_ID, CLIENT_SECRET)

    b64_auth_str = base64.urlsafe_b64encode(auth_str.encode()).decode()

    headers = {"Content-Type" : HEADER, "Authorization" : "Basic {}".format(b64_auth_str)} 

    post = requests.post(SPOTIFY_URL_TOKEN, params=body, headers=headers)
    return handleToken(json.loads(post.text))
    

def handleToken(response):
    #print(response)
    auth_head = {"Authorization": "Bearer {}".format(response["access_token"])}
    REFRESH_TOKEN = response["refresh_token"]
    return [response["access_token"], auth_head, response["scope"], response["expires_in"]]


def refreshAuth():
    body = {
        "grant_type" : "refresh_token",
        "refresh_token" : REFRESH_TOKEN
    }

    post_refresh = requests.post(SPOTIFY_URL_TOKEN, data=body, headers=HEADER)
    p_back = json.dumps(post_refresh.text)
    
    return handleToken(p_back)



    
def getUser():
    return getAuth(CLIENT_ID, CALLBACK_URL, SCOPE)

def getUserToken(code):
    global TOKEN_DATA
    TOKEN_DATA = getToken(code, CLIENT_ID, CLIENT_SECRET, CALLBACK_URL)
 
def refreshToken(time):
    time.sleep(time)
    TOKEN_DATA = refreshAuth()

def getAccessToken():
    return TOKEN_DATA