# spotify-github-profile

Create Spotify now playing card on your github profile

Running on Vercel serverless function, store data in Firebase (store only access_token, refresh_token, token_expired_timestamp)

Table of Contents  
[Connect And Grant Permission](#connect-and-grant-permission)  
[Example](#example)  
[Running for development locally](#running-for-development-locally)  
[Setting up Vercel](#setting-up-vercel)  
[Setting up Firebase](#setting-up-firebase)  
[Setting up Spotify dev](#setting-up-spotify-dev)  
[Running locally](#running-locally)  
[How to Contribute](#how-to-contribute)  
[Known Bugs](#known-bugs)  
[Features in Progress](#features-in-progress)  
[Credit](#credit)  


## Connect And Grant Permission

- Click `Connect with Spotify` button below to grant permission

[<img src="/img/btn-spotify.png">](https://spotify-github-profile.vercel.app/api/login)

## Example

- Default theme

![spotify-github-profile](/img/default.svg)

- Compact theme

![spotify-github-profile](/img/compact.svg)

- Natemoo-re theme

![spotify-github-profile](/img/natemoo-re.svg)

- Novatorem theme

![spotify-github-profile](/img/novatorem.svg)

- Karaoke theme

![spotify-github-profile](/img/karaoke.svg)



## Running for development locally

To develop locally, you need:

- A fork of this project as your repository
- A Vercel project connected with the forked repository
- A Firebase project with Cloud Firestore setup
- A Spotify developer account

### Setting up Vercel

- [Create a new Vercel project by importing](https://vercel.com/import) the forked project on GitHub

### Setting up Firebase

- Create [a new Firebase project](https://console.firebase.google.com/u/0/)
- Create a new Cloud Firestore in the project
- Download configuration JSON file from _Project settings_ > _Service accounts_ > _Generate new private key_
- Convert private key content as BASE64
  - You can use Encode/Decode extension in VSCode to do so
  - This key will be used in step explained below

### Setting up Spotify dev

- Login to [developer.spotify.com](https://developer.spotify.com/dashboard/applications)
- Create a new project
- Edit settings to add _Redirect URIs_
  - add `http://localhost:3000/api/callback`

### Running locally

- Install [Vercel command line](https://vercel.com/download) with `npm i -g vercel`
- Create `.env` file at the root of the project and paste your keys in `SPOTIFY_CLIENT_ID`, `SPOTIFY_SECRET_ID`, and `FIREBASE`

```sh
BASE_URL='http://localhost:3000/api'
SPOTIFY_CLIENT_ID='____'
SPOTIFY_SECRET_ID='____'
FIREBASE='__BASE64_FIREBASE_JSON_FILE__'
```

- Run `vercel dev`

```sh
$ vercel dev
Vercel CLI 20.1.2 dev (beta) — https://vercel.com/feedback
> Ready! Available at http://localhost:3000
```

- Now try to access http://localhost:3000/api/login

## How to Contribute

- Develop locally and submit a pull request!
- Submit newly encountered bugs to the [Issues](https://github.com/kittinan/spotify-github-profile/issues) page
- Submit feature suggestions to the [Issues](https://github.com/kittinan/spotify-github-profile/issues) page, with the label [Feature Suggestion]

## Known Bugs

[404/500 Error when playing local files](https://github.com/kittinan/spotify-github-profile/issues/19)

## Features in Progress

[Cross-platform support (Pandora, Apple Music, etc.)](https://github.com/kittinan/spotify-github-profile/issues/37)

## Credit

Inspired by https://github.com/natemoo-re
