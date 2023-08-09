import streamlit_authenticator as stauth
import yaml

def update_yaml_passwords(file_path, updated_credentials):
    with open(file_path, 'r') as file:
        yaml_content = yaml.safe_load(file)

    if 'credentials' in yaml_content:
        usernames = yaml_content['credentials'].get('usernames', {})

        for user, details in usernames.items():
            if user in updated_credentials:
                yaml_content['credentials']['usernames'][user]['password'] = updated_credentials[user]
                #details['password'].set(updated_passwords[user])

    with open(file_path, 'w') as file:
        yaml.dump(yaml_content, file)

def get_yaml_passwords(file_path):
    with open(file_path, 'r') as file:
        yaml_content = yaml.safe_load(file)

    passwords = []
    if 'credentials' in yaml_content:
        usernames = yaml_content['credentials'].get('usernames', {})

        for user, details in usernames.items():
            password = details.get('password')
            passwords.append({'username': user, 'password': password})

    return passwords

file_path = 'credentials.yml'

credentials = get_yaml_passwords(file_path)
print(credentials)
updated_credentials = {}

for cred in credentials:
    hashed_pwd = stauth.Hasher([cred["password"]]).generate()
    updated_credentials[cred["username"]]=hashed_pwd[0]

print(updated_credentials)
update_yaml_passwords(file_path, updated_credentials)