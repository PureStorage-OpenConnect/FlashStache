"""FlashArray Monitoring Tasks."""

import datetime
import logging
import os
import purestorage
import pytz
import urllib3

from django_rq import job
from django.db import IntegrityError
from django.core.exceptions import FieldError, ObjectDoesNotExist
from flasharray import models

# TODO: Actually set up certificate/authority instead of suppressing this warning:
urllib3.disable_warnings()
logger = logging.getLogger('flash_stache')


@job
def get_from_api(hostname, ip_address, api_token, requests):
    """Retrieve API information for one or more requests.

    Arguments:
        hostname (str): Alias/hostname of a FlashArray.
        ip_address (str): A FlashArray's IP address to connect to.
        api_token (str): A valid API Token for the FlashArray.
        requests (dict): One or more API list/get requests with/without arguments.

    Returns:
        result (str): A (multi-line) result string which will be used in django-rq job status.
    """
    logger.info('Getting data from {} at {}.'.format(hostname, ip_address))
    try:
        connection = purestorage.FlashArray(ip_address, api_token=api_token)
    except purestorage.PureHTTPError as error:
        logger.error('Failed to connect to: {}.\n{}'.format(hostname, error))
        return
    results = []
    for request in requests:
        if request not in models.API_REQUESTS:
            logger.error('Invalid API Request: "{}".'.format(request))
        action = models.API_REQUESTS[request]['action']
        call = models.API_REQUESTS[request]['call']
        class_name = models.API_REQUESTS[request]['class']
        # pylint: disable=protected-access
        try:
            response = connection._request('GET', call)
        except purestorage.PureHTTPError as error:
            logger.error('Failed API request: {} to {}.\n{}'.format(request, hostname, error))
            response = None
        if not response:
            logger.info('Empty response from {} for request: {}'.format(hostname, request))
            continue
        elif not isinstance(response, list):
            response = [response]
        result = ''
        if class_name == 'ReplicationTransfers':
            for snapshot in sorted(response, key=lambda entry: entry['created'], reverse=True):
                snap_name = snapshot.get('name')
                # pylint: disable=no-member
                if models.ReplicationTransfers.objects.filter(name=snap_name).all():
                    # This snapshot is already saved in the database, don't save a duplicate.
                    # Break the loop (as subsequent snapshots will have already been saved)
                    break
                result = save_result(response, hostname, class_name)
        elif action == 'save':
            try:
                result = save_result(response, hostname, class_name)
            except TypeError as error:
                result = 'Failed to save {} for {}.\n{}'.format(request, hostname, error)
                logger.error(result)
        else:
            result = update_result(response, hostname, class_name)
        results.append(result)
    logger.debug(', '.join(list(set(results))))


def save_result(response, hostname, class_name):
    """Save an API response based upon class_name."""
    logger.info('Saving response for {} from {}.'.format(class_name, hostname))
    results = []
    for values in response:
        if class_name == 'RemoteAssist':  # Change disabled/enabled to False/True.
            if values['status'] == 'enabled':
                values['status'] = True
            else:
                values['status'] = False
        elif class_name == 'ReplicationPeer':
            if 'array_name' in values:
                name = values.get('array_name')
                values['name'] = name
                del values['array_name']
        if 'hostname' not in values:
            values['hostname'] = hostname
        instance = getattr(models, class_name)(**values)
        try:
            instance.save()
            result = 'Saved to {} for {}.'.format(class_name, hostname)
            logger.debug(result)
            results.append(result)
        except (TypeError, IntegrityError) as error:
            result = 'Failed to save to {} for {}.\n{}'.format(class_name, hostname, error)
            logger.error(result)
            results.append(result)
    return ', '.join(list(set(results)))


def update_result(response, hostname, class_name):
    """Update table based upon class_name with the API result."""
    logger.info('Updating response for {} from {}.'.format(class_name, hostname))
    results = []
    if class_name == 'RemoteAssist':
        logger.info('The reponse: {}'.format(response))
    for values in response:
        if class_name == 'RemoteAssist':  # Change disabled/enabled to False/True.
            if values['status'] == 'enabled':
                values['status'] = True
            else:
                values['status'] = False
        elif class_name == 'ReplicationPeer':
            if 'array_name' in values:
                name = values.get('array_name')
                values['name'] = name
                del values['array_name']
        if 'hostname' not in values:
            values['hostname'] = hostname
        try:
            # Overwrite the last_state with the new state:
            try:
                matches = getattr(models, class_name).objects.filter(hostname=hostname,
                                                                     name=values.get('name')).all()
                if len(matches) > 0:
                    # Negative indexing is not supported...
                    last = matches[0]
            except FieldError:
                continue
            for key, value in values.iteritems():
                setattr(last, key, value)
            last.save()
            result = 'Updated {} for {}.'.format(class_name, hostname)
            logger.debug(result)
            results.append(result)
        except (ObjectDoesNotExist, UnboundLocalError):  # No state exists, just save one instead.
            try:
                results = save_result(response, hostname, class_name)
            except TypeError as error:
                logger.error('Failed to save {} for {}.\n{}'.format(class_name, hostname, error))
            break
    return ', '.join(list(set(results)))


@job
def clean_database(hostname, requests, retention_hours):
    """Clean out database entries based upon retention time."""
    logger.info('Evaluating database for cleanup for {}.'.format(hostname))
    now = datetime.datetime.utcnow()
    cutoff = (now - datetime.timedelta(hours=retention_hours)).replace(tzinfo=pytz.UTC)
    logger.info('Cleaning database at {} with cutoff at {}.'.format(now, cutoff))
    for request in requests:
        class_name = getattr(models, models.API_REQUESTS[request]['class'])
        # Delete all rows which are greater than the cutoff timestamp
        try:
            class_name.objects.filter(hostname=hostname, time__gte=cutoff).delete()
        except FieldError as error:
            error_str = 'Failed to clean database: {} for {}.\n{}'
            logger.debug(error_str.format(class_name, hostname, error))
            continue
        logger.debug('Deleting {} for FlashArray {}.'.format(class_name, hostname))
    return 'Completed (Database Clean-up): {} for {}.'.format(', '.join(requests), hostname)


def get_logs(log_file='./flasharray/flash_stache.log', cutoff=100):
    """Get last 'n' lines from the log_file."""
    if not os.path.isfile(log_file):
        logger.error('Failed to find log file: {}'.format(log_file))
        lines = []
    else:
        with open(log_file, 'r') as readable:
            lines = readable.readlines()[-cutoff:]  # Just get the last 'n' lines.
    return lines
