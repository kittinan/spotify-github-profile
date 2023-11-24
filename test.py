import requests

def get_number_of_pull_requests(username):
    response = requests.get(f'https://api.github.com/users/{username}/events/public')
    response.raise_for_status()  \

    events = response.json()
    pull_request_events = [event for event in events if event['type'] == 'PullRequestEvent']

    return len(pull_request_events)

username = 'oscarmmv'  
print(get_number_of_pull_requests(username))