"""Perform a basic configuration of Grafana."""

import argparse

from grafana_api_client import GrafanaClient, GrafanaClientError, GrafanaUnauthorizedError


def main():
    """Perform a basic configuration of the local Grafana Server."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-u', '--user', default='root', nargs='?')
    parser.add_argument('-c', '--current_password', default='admin')
    parser.add_argument('-p', '--new_password')
    args = parser.parse_args()
    client = GrafanaClient(('admin', args.current_password), host='127.0.0.1', port=3000)
    payload = {'name': 'mysql-default',
               'isDefault': True,
               'type': 'mysql',
               'url': 'localhost:3306',
               'user': args.user,
               'password': args.new_password,
               'database': 'flash_stache',
               'access': 'proxy'}
    try:
        result = client.datasources.create(**payload)['message']
    except (GrafanaClientError, GrafanaUnauthorizedError) as error:
        result = 'Failed to add the default datasource.\n{}'.format(error)
    print result
    # Update the admin password:
    pass_payload = {
        'oldPassword': args.current_password,
        'newPassword': args.new_password,
        'confirmNew': args.new_password,
    }
    try:
        result = client.make_raw_request('PUT', 'user/password', pass_payload)['message']
    except (GrafanaClientError, GrafanaUnauthorizedError) as error:
        result = 'Failed to update the password for the Grafana admin user.\n{}'.format(error)
    print result


if __name__ == '__main__':
    main()
