# spotify-github-profile

Create Spotify now playing card on your github profile

Running on Vercel serverless function, store data in Firebase (store only access_token, refresh_token, token_expired_timestamp)

## Connect & Grant Permission

- Click `Connect with Spotify` button below to grant permission

[<img src="/img/btn-spotify.png">](https://spotify-github-profile.vercel.app/api/login)

## Example

![spotify-github-profile](/img/example.svg)

## Running for development

- [Vercel command line](https://vercel.com/download)
- Create .env file

```sh
SPOTIFY_CLIENT_ID='___'
SPOTIFY_SECRET_ID='____'
BASE_URL='http://localhost:3000/api'
FIREBASE='__BASE64_FIREBASE_JSON_FILE__'
```

- Run vercel dev

```
vercel dev
```

## Credit

Inspired by https://github.com/natemoo-re
