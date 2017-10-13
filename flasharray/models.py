"""Pure FlashArray API Monitoring Models."""

import datetime
import logging
import re
import os

from distutils.version import LooseVersion

import django_rq
import purestorage

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from model_utils.models import TimeStampedModel
from multiselectfield import MultiSelectField

logger = logging.getLogger('flash_stache')

API_REQUESTS = {
    # Action will be used for database management
    # Save will append row(s)
    # Update will overwrite row(s)
    'array_alerts': {
        'action': 'save',
        'call': 'message?recent=true',
        'class': 'ArrayAlert',
    },
    'array_performance': {
        'action': 'save',
        'call': 'array?action=monitor',
        'class': 'ArrayPerformance',
    },
    'array_status': {
        'action': 'update',
        'call': 'array?controllers=true',
        'class': 'ArrayStatus',
    },
    'array_space': {
        'action': 'save',
        'call': 'array?space=true',
        'class': 'ArraySpace',
    },
    'host_connections': {
        'action': 'update',
        'call': 'host',
        'class': 'Host',
    },
    'host_details': {
        'action': 'update',
        'call': 'host?all=true',
        'class': 'HostDetails',
    },
    'host_performance': {
        'action': 'save',
        'call': 'host?action=monitor',
        'class': 'HostPerformance',
    },
    'host_space': {
        'action': 'save',
        'call': 'host?space=true',
        'class': 'HostSpace',
    },
    'hgroup_connections': {
        'action': 'update',
        'call': 'hgroup',
        'class': 'HostGroup',
    },
    'hgroup_performance': {
        'action': 'save',
        'call': 'hgroup?action=monitor',
        'class': 'HostGroupPerformance',
    },
    'hgroup_space': {
        'action': 'save',
        'call': 'hgroup?space=true',
        'class': 'HostGroupSpace',
    },
    'port_connections': {
        'action': 'update',
        'call': 'port?initiators=true',
        'class': 'Port',
    },
    #'purity_apps': {
    #    'action': 'update',
    #    'call': 'app',
    #    'class': 'PurityApp',
    #},
    'remote_assist': {
        'action': 'update',
        'call': 'array/remoteassist',
        'class': 'RemoteAssist',
    },
    'replication_peers': {
        'action': 'update',
        'call': 'array/connection',
        'class': 'ReplicationPeer',
    },
    'replication_transfers': {
        'action': 'update',
        # This one requires heavy post-processing as it returns all history of snapshot transfers.
        'call': 'pgroup?snap=true&transfer=true',
        'class': 'ReplicationTransfers',
    },
    'volume_performance': {
        'action': 'save',
        'call': 'volume?action=monitor',
        'class': 'VolumePerformance',
    },
    'volume_space': {
        'action': 'save',
        'call': 'volume?space=true&snap=true',
        'class': 'VolumeSpace'
    },
}


def _header(string):
    """Make API REQUEST strings human readable."""
    # Example: volume_space -> Volume Space
    camelized = []
    split = string.split('_')
    for word in split:
        word = word.lower()
        camel = word[0].upper() + word[1:]
        camelized.append(camel)
    return ' '.join(camelized)


TEMPLATES = os.listdir(os.path.join(os.path.dirname(__file__), 'grafana_templates'))
DASHES = [(template, _header(template)) for template in [item.split('.')[0] for item in TEMPLATES]]
INTERVALS = ((5, '5 seconds'),
             (30, '30 seconds'),
             (60, '60 seconds'))
NETWORK_SERVICES = (('iscsi', 'iscsi'),
                    ('management', 'management'),
                    ('replication', 'replication'))
RETENTIONS = ((24, '24 hours'), (48, '48 hours'), (72, '72 hours'))


class FlashArray(TimeStampedModel):
    """A Pure FlashArray form which will be used for validation/web-interface/database/etc."""
    alphanumeric = RegexValidator(r'\.|\,|\\|\/|\%|\*',
                                  'Hostname cannot contain SQL special characters such as: .,%\/*.',
                                  inverse_match=True)
    calls = tuple([(key, _header(key)) for key in sorted(API_REQUESTS.keys())])
    hostname = models.CharField(max_length=100, unique=True, help_text='A Unique Name',
                                validators=[alphanumeric], primary_key=True)
    ip_address = models.GenericIPAddressField(unique=True,
                                              help_text='The IP Address of vir0 is recommended')
    # REST API tokens are 36 characters long (including - delimiters).
    api_token = models.CharField(max_length=36, help_text='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx')
    interval = models.PositiveIntegerField('Interval', choices=INTERVALS, default=30)
    retention_hours = models.IntegerField('Database Retention', choices=RETENTIONS, default=24)
    default_dashes = [item[0].split('.')[0] for item in DASHES] or 'No dashboards found'
    dashboards = MultiSelectField(choices=DASHES, null=True, default=default_dashes)
    enabled = models.BooleanField('Enabled', default=True)
    # Read-only Fields
    date_added = models.DateTimeField(auto_now_add=True, editable=False)
    queue = models.CharField('queue', max_length=16, default='default', editable=False)
    db_job_id = models.CharField('db job id', max_length=128, editable=False, blank=True, null=True)
    job_id = models.CharField('job id', max_length=128, editable=False, blank=True, null=True)
    requests = MultiSelectField(choices=calls, default=[item[0] for item in calls], editable=False)

    def __str__(self):
        return self.hostname

    def clean(self):
        """Custom clean method to test a connection attempt to the API for validation."""
        super(FlashArray, self).clean()
        self.hostname = self.hostname.lower()
        try:
            connection = purestorage.FlashArray(self.ip_address, api_token=self.api_token)
            api_version = connection.get_rest_version()
            if LooseVersion(api_version) < LooseVersion('1.6'):
                message = 'Found API Version {} (1.6+ is required).  Consider upgrading Purity.'
                raise ValidationError(message.format(api_version))
        except purestorage.PureError:
            message = 'Failed to connect to {}.  Please verify IP Address and API Token.'
            raise ValidationError(message.format(self.ip_address))

    def delete(self, *args, **kwargs):
        # Unschedule running jobs.
        self.unschedule()
        # Clean-out entries in all related database tables.
        # TODO: This may need to be done manually, select_related isn't finding everything.
        # FlashArray.objects.filter(hostname=self.hostname).select_related().delete()
        super(FlashArray, self).delete(*args, **kwargs)

    def is_scheduled(self):
        """Check if a job is scheduled via job_id."""
        return self.job_id in self.fetch_scheduler()

    def save(self, **kwargs):
        """Save the FlashArray information to DB."""
        self.unschedule()
        if self.enabled:
            self.schedule()
        super(FlashArray, self).save(**kwargs)
        logger.info('Saved job {} for {}.'.format(self.job_id, self.hostname))

    def schedule(self):
        """Schedule a job/add it to the schedule DB."""
        if not self.enabled:
            return False
        scheduler = self.fetch_scheduler()
        # Check if there are jobs already running for this array; if so unschedule them.
        self.unschedule()
        kwargs = {'hostname': self.hostname,
                  'ip_address': self.ip_address,
                  'api_token': self.api_token,
                  'requests': self.requests}
        job = scheduler.schedule(func='flasharray.tasks.get_from_api',
                                 kwargs=kwargs,
                                 interval=self.interval,
                                 scheduled_time=datetime.datetime.utcnow(),
                                 repeat=None)  # Repeat indefinitely
        self.job_id = job.id
        logger.info('Scheduled API job: {} for {}.'.format(job.id, self.hostname))
        # Schedule a database clean-up job as well:
        db_job = scheduler.schedule(func='flasharray.tasks.clean_database',
                                    kwargs={'hostname': self.hostname,
                                            'requests': self.requests,
                                            'retention_hours': self.retention_hours},
                                    interval=86400,  # 24 hours in seconds
                                    scheduled_time=datetime.datetime.utcnow(),
                                    repeat=None)  # Repeat indefinitely
        logger.info('Scheduled clean-up job: {} for {}.'.format(db_job.id, self.hostname))
        self.db_job_id = db_job.id
        return True

    def fetch_scheduler(self):
        """Fetch the scheduler for the assigned queue."""
        return django_rq.get_scheduler(self.queue)

    def unschedule(self):
        """Unschedule a job via job_id."""
        if self.is_scheduled():
            self.fetch_scheduler().cancel(self.job_id)
            self.fetch_scheduler().cancel(self.db_job_id)
            logger.info('Cancelled job: {} for {}.'.format(self.job_id, self.hostname))
            logger.info('Cancelled job: {} for {}.'.format(self.db_job_id, self.hostname))
        self.job_id = None
        self.db_job_id = None
        return True

    def get_absolute_url(self):
        """Return to home after editing/deleting/etc."""
        return '/flasharray/home.html'

    class Meta:
        """Metadata for displaying/ordering information regarding FlashArray(s)."""
        ordering = ('hostname',)
        verbose_name = 'Pure FlashArray'


# Helper Models:
class GenericConnection(models.Model):
    """A FlashArray Connection."""
    name = models.CharField(max_length=255, null=True)


class IPAddress(models.Model):
    """An Ethernet IP Address."""
    address = models.GenericIPAddressField(unique=True)


class IQN(models.Model):
    """An IQN Address."""
    address = models.CharField(max_length=255, unique=True, null=True)


class Volume(models.Model):
    """A FlashArray volume."""
    name = models.CharField(max_length=255, default='', null=True, unique=True)
    created = models.DateTimeField()
    size = models.BigIntegerField()
    source = models.CharField(max_length=255, null=True)


class WWN(models.Model):
    """A WWN Address."""
    address = models.CharField(max_length=64, unique=True, null=True)

    def clean(self):
        """Custom Validation for WWN structure."""
        super(WWN, self).clean()
        wwn_pattern = re.compile(r'(\w\w:){7}\w\w')
        # 21:00:00:e0:8b:05:05:04
        if not wwn_pattern.match(self.address):
            raise ValidationError('WWN is malformed: {}.'.format(self.address))


# Rest API Responses:
class ArrayAlert(models.Model):
    """An Alert from a FlashArray."""
    actual = models.CharField(max_length=255, null=True)
    category = models.CharField(max_length=255, null=True)
    code = models.PositiveIntegerField()
    component_name = models.CharField(max_length=255, null=True)
    component_type = models.CharField(max_length=255, null=True)
    current_severity = models.CharField(max_length=255, null=True)
    details = models.CharField(max_length=255, null=True)
    event = models.CharField(max_length=255, null=True)
    expected = models.CharField(max_length=255, null=True)
    id = models.PositiveIntegerField()
    hostname = models.CharField(max_length=255)
    opened = models.DateTimeField()
    # Cannot use the built-in 'id' due to conflict with Alert 'id'.
    row_id = models.AutoField(primary_key=True)
    time = models.DateTimeField(null=True)


class ArraySpace(models.Model):
    """Array-wide space metrics."""
    capacity = models.BigIntegerField(default=0)
    data_reduction = models.FloatField(default=0.0)
    hostname = models.CharField(max_length=255)
    parity = models.FloatField(default=0.0)
    shared_space = models.BigIntegerField(default=0)
    snapshots = models.BigIntegerField(default=0)
    system = models.BigIntegerField(default=0)
    thin_provisioning = models.FloatField(default=0.0)
    time = models.DateTimeField(auto_now=True)
    total = models.BigIntegerField(default=0)
    total_reduction = models.FloatField(default=0.0)
    volumes = models.BigIntegerField(default=0)


class ArrayStatus(models.Model):
    """Array Controllers Status."""
    hostname = models.CharField(max_length=255)
    mode = models.CharField(max_length=16)
    model = models.CharField(max_length=32)
    name = models.CharField(max_length=32)
    status = models.CharField(max_length=32)
    version = models.CharField(max_length=32)


class Host(models.Model):
    """A single host connected to a FlashArray."""
    hgroup = models.CharField(max_length=255, null=True)
    hostname = models.CharField(max_length=255, default='')
#    iqn = models.ManyToManyField(IQN, blank=True)
    iqn = models.CharField(max_length=512, null=True)
    name = models.CharField(max_length=255)
#    wwn = models.ManyToManyField(WWN, blank=True)
    wwn = models.CharField(max_length=512, null=True)


class HostDetails(models.Model):
    """A single host with connection details."""
#    hgroup = models.ManyToManyField(HostGroup, blank=True)
    hgroup = models.CharField(max_length=255, null=True, default='')
    hostname = models.CharField(max_length=255, default='')
#    host_iqn = models.ManyToManyField(IQN, blank=True)
    host_iqn = models.CharField(max_length=255, null=True, default='')
    lun = models.CharField(max_length=255, null=True, default='')
    name = models.CharField(max_length=255, null=True, default='')
#    host_wwn = models.ManyToManyField(WWN, blank=True)
    host_wwn = models.CharField(max_length=255, null=True, default='')
    target_port = models.CharField(max_length=255, null=True, default='')
#    vol = models.ManyToManyField(Volume, blank=True)
    vol = models.CharField(max_length=255, null=True, default='')


class HostGroup(models.Model):
    """A single host group connected to a FlashArray."""
    hostname = models.CharField(max_length=255, default='')
    hosts = models.CharField(max_length=1024, default='')
    name = models.CharField(max_length=255)


class Port(models.Model):
    """A external Port on the FlashArray."""
    failover = models.CharField(max_length=255, null=True)
    hostname = models.CharField(max_length=255, default='')
#    iqn = models.ManyToManyField(IQN, blank=True)
    iqn = models.CharField(max_length=512, null=True)
    portal = models.CharField(max_length=255, null=True)
    target = models.CharField(max_length=255, null=True)
    target_iqn = models.CharField(max_length=512, null=True)
    target_wwn = models.CharField(max_length=512, null=True)
    target_portal = models.CharField(max_length=255, null=True)
#    wwn = models.ManyToManyField(WWN, blank=True)
    wwn = models.CharField(max_length=512, null=True)


class RemoteAssist(models.Model):
    """Remote Assist connection status."""
    hostname = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    port = models.CharField(max_length=255, null=True)
    status = models.BooleanField()


class ReplicationPeer(models.Model):
    """Async Replication Peers."""
    name = models.CharField(max_length=255)
    connected = models.BinaryField()
    hostname = models.CharField(max_length=255)
    id = models.CharField(max_length=36)
    management_address = models.CharField(max_length=255, default='', null=True)
    replication_address = models.CharField(max_length=255, default='', null=True)
    # Cannot use the built-in 'id' due to conflict with Peer 'id'.
    row_id = models.AutoField(primary_key=True)
    throttled = models.BinaryField()
    time = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=255, null=True)
#    type = models.ManyToManyField(Connection, blank=True)
    version = models.CharField(max_length=25)


class ReplicationTransfers(models.Model):
    """Async Replication Snapshot Transfers."""
    completed = models.DateTimeField(null=True)
    created = models.DateTimeField(null=True)
    data_transferred = models.BigIntegerField(null=True, default=0)
    hostname = models.CharField(max_length=255)
    name = models.CharField(max_length=255, unique=True)
    physical_bytes_written = models.BigIntegerField(null=True, default=0)
    progress = models.FloatField(null=True, default=0.0)
    queued = models.DateTimeField(null=True)
    source = models.CharField(max_length=255)
    started = models.DateTimeField(null=True)
    time = models.DateTimeField(auto_now=True)
    transfer_delay = models.BigIntegerField(null=True, default=0.0)


class HostSpace(models.Model):
    """Per Host Space Metrics."""
    hostname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    snapshots = models.BigIntegerField(default=0)
    time = models.DateTimeField(auto_now=True)
    total = models.BigIntegerField(default=0)
    volumes = models.BigIntegerField(default=0)
    data_reduction = models.FloatField(default=0.0)
    thin_provisioning = models.FloatField(default=0.0)
    total_reduction = models.FloatField(default=0.0)


class HostGroupSpace(models.Model):
    """Per Host Group Space Metrics."""
    hostname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    snapshots = models.BigIntegerField(default=0)
    time = models.DateTimeField(auto_now=True)
    total = models.BigIntegerField(default=0)
    volumes = models.BigIntegerField(default=0)
    data_reduction = models.FloatField(default=0.0)
    thin_provisioning = models.FloatField(default=0.0)
    total_reduction = models.FloatField(default=0.0)


class VolumeSpace(models.Model):
    """Per Volume Space Metrics."""
    hostname = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    snapshots = models.BigIntegerField(default=0)
    time = models.DateTimeField(auto_now=True)
    total = models.BigIntegerField(default=0)
    volumes = models.BigIntegerField(default=0)


# Duplicate Tables:
# TODO: Need to find a way to make these inherit to remove redundancy
class ArrayPerformance(models.Model):
    """This exists in order to create a distinct database table."""
    hostname = models.CharField(max_length=255)
    input_per_sec = models.FloatField(default=0.0)
    name = models.CharField(max_length=255)
    output_per_sec = models.FloatField(default=0.0)
    queue_depth = models.FloatField(default=0.0)
    reads_per_sec = models.FloatField(default=0.0)
    time = models.DateTimeField(auto_now=True)
    usec_per_read_op = models.FloatField(default=0.0)
    usec_per_write_op = models.FloatField(default=0.0)
    writes_per_sec = models.FloatField(default=0.0)
    san_usec_per_read_op = models.FloatField(default=0.0, null=True)
    san_usec_per_write_op = models.FloatField(default=0.0, null=True)


class HostPerformance(models.Model):
    """This exists in order to create a distinct database table."""
    hostname = models.CharField(max_length=255)
    input_per_sec = models.FloatField(default=0.0)
    name = models.CharField(max_length=255)
    output_per_sec = models.FloatField(default=0.0)
    queue_depth = models.FloatField(default=0.0)
    reads_per_sec = models.FloatField(default=0.0)
    time = models.DateTimeField(auto_now=True)
    usec_per_read_op = models.FloatField(default=0.0)
    usec_per_write_op = models.FloatField(default=0.0)
    writes_per_sec = models.FloatField(default=0.0)
    san_usec_per_read_op = models.FloatField(default=0.0, null=True)
    san_usec_per_write_op = models.FloatField(default=0.0, null=True)


class HostGroupPerformance(models.Model):
    """This exists in order to create a distinct database table."""
    hostname = models.CharField(max_length=255)
    input_per_sec = models.FloatField(default=0.0)
    name = models.CharField(max_length=255)
    output_per_sec = models.FloatField(default=0.0)
    queue_depth = models.FloatField(default=0.0)
    reads_per_sec = models.FloatField(default=0.0)
    time = models.DateTimeField(auto_now=True)
    usec_per_read_op = models.FloatField(default=0.0)
    usec_per_write_op = models.FloatField(default=0.0)
    writes_per_sec = models.FloatField(default=0.0)
    san_usec_per_read_op = models.FloatField(default=0.0, null=True)
    san_usec_per_write_op = models.FloatField(default=0.0, null=True)


class VolumePerformance(models.Model):
    """This exists in order to create a distinct database table."""
    hostname = models.CharField(max_length=255)
    input_per_sec = models.FloatField(default=0.0)
    name = models.CharField(max_length=255)
    output_per_sec = models.FloatField(default=0.0)
    queue_depth = models.FloatField(default=0.0)
    reads_per_sec = models.FloatField(default=0.0)
    time = models.DateTimeField(auto_now=True)
    usec_per_read_op = models.FloatField(default=0.0)
    usec_per_write_op = models.FloatField(default=0.0)
    writes_per_sec = models.FloatField(default=0.0)
    san_usec_per_read_op = models.FloatField(default=0.0, null=True)
    san_usec_per_write_op = models.FloatField(default=0.0, null=True)
