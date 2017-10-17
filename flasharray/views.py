"""Views/Pages."""

import logging
import socket

from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.shortcuts import render
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from flasharray import models
from flasharray import tasks

logger = logging.getLogger('flash_stache')


@login_required(login_url='flasharray/login')
def index(request):
    """Generate a list of FlashArray objects ordered by hostname for the base page."""
    # pylint: disable=no-member
    ip_addr = socket.gethostbyname(socket.gethostname())
    context = {
        'arrays': models.FlashArray.objects.distinct(),
        'remote_assist': models.RemoteAssist.objects.distinct(),
        'array_status': models.ArrayStatus.objects.distinct(),
        'url': 'http://{}'.format(ip_addr),
        'grafana': 'http://{}:3000'.format(ip_addr),
    }
    logger.info('Loaded Home Page.')
    return render(request, 'home.html', context)


def logs(request):
    """Fetch log_files for displaying most recent contents."""
    log_files = tasks.get_logs()
    context = {'logs': log_files}
    logger.info('Loaded Logs Page.')
    return render(request, 'logs.html', context=context)


class FlashArrayForm(ModelForm):
    """Base form for creating/modifying a FlashArray."""
    class Meta:
        model = models.FlashArray
        fields = ['hostname',
                  'ip_address',
                  'api_token',
                  'interval',
                  'retention_hours',
                  'enabled',
                  'dashboards']


class FlashArrayCreate(CreateView):
    """Simple view for Creating a FlashArray."""
    fields = '__all__'
    form = FlashArrayForm
    model = models.FlashArray
    template_name_suffix = '_create_form'
    success_url = '/flasharray/home.html'


class FlashArrayDelete(DeleteView):
    """Simple view for Deleting a FlashArray."""
    fields = '__all__'
    form = FlashArrayForm
    model = models.FlashArray
    template_name_suffix = '_delete_form'
    success_url = '/flasharray/home.html'


class FlashArrayUpdate(UpdateView):
    """Simple view for Updating a FlashArray."""
    fields = ['interval', 'retention_hours', 'enabled', 'dashboards']
    form = FlashArrayForm
    model = models.FlashArray
    template_name_suffix = '_update_form'
    success_url = '/flasharray/home.html'

