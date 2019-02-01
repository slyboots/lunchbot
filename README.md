# lunchbot
small service for the team to help keep track of who is at lunch

### Developing

- __Requirements:__

    - AWS EB CLI
    - ngrok
    - pipenv

__Instructions:__
    - Open terminal in project dir
    - Run `pipenv install --dev`
    - Run `pipenv run flask init-db
    - Run `pipenv run flask start`
    - In a separate terminal, run `ngrok http 5000`
    - Update the App's settings in Slack to point to the ngrok URL that was generated
    - Send GET request to the `/ping` endpoint to confirm everything is working
