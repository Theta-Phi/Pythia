import sys
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

def main():
    try:
        file_path = sys.argv[1]
    except:
        print(f'you must specify the relative path to the credentials file .e.g. credentials_example.yml')
        sys.exit()

    try:
        credentials = get_yaml_passwords(file_path)
        updated_credentials = {}
    except:
        print(f'failed to read the specified credentials file check path, filename and formatting')
        sys.exit()

    for cred in credentials:
        hashed_pwd = stauth.Hasher([cred["password"]]).generate()
        updated_credentials[cred["username"]]=hashed_pwd[0]

    try:
        update_yaml_passwords(file_path, updated_credentials)
        print('Credentials file updated with hashed password...')
    except:
        print(f'failed to update the credentials file with the hashed passwords - check document formatting and keys')

if __name__ == '__main__':
    main()